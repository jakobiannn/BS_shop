from http import HTTPStatus

from aiohttp.web_exceptions import HTTPNotFound
from aiohttp.web_response import Response
from aiohttp_apispec import docs, request_schema, response_schema
from asyncpg import ForeignKeyViolationError
from marshmallow import ValidationError
from sqlalchemy import and_, or_

from shop.api.schema import PatchCitizenResponseSchema, PatchShopUnitSchema
from shop.db.schema import units_table

from .base import BaseImportView
from .query import CITIZENS_QUERY


class CitizenView(BaseImportView):
    URL_PATH = r'/imports/{import_id:\d+}/citizens/{unit_id:\d+}'

    @property
    def citizen_id(self):
        return int(self.request.match_info.get('unit_id'))

    @staticmethod
    async def acquire_lock(conn, import_id):
        await conn.execute('SELECT pg_advisory_xact_lock($1)', import_id)

    @staticmethod
    async def get_citizen(conn, import_id, citizen_id):
        query = CITIZENS_QUERY.where(and_(
            units_table.c.import_id == import_id,
            units_table.c.unit_id == citizen_id
        ))
        return await conn.fetchrow(query)

    @classmethod
    async def update_citizen(cls, conn, import_id, citizen_id, data):
        values = {k: v for k, v in data.items() if k != 'relatives'}
        if values:
            query = units_table.update().values(values).where(and_(
                units_table.c.import_id == import_id,
                units_table.c.unit_id == citizen_id
            ))
            await conn.execute(query)

    @docs(summary='Обновить указанного жителя в определенной выгрузке')
    @request_schema(PatchShopUnitSchema())
    @response_schema(PatchCitizenResponseSchema(), code=HTTPStatus.OK.value)
    async def patch(self):
        # Транзакция требуется чтобы в случае ошибки (или отключения клиента,
        # не дождавшегося ответа) откатить частично добавленные изменения, а
        # также для получения транзакционной advisory-блокировки.
        async with self.pg.transaction() as conn:

            # Блокировка позволит избежать состояние гонки между конкурентными
            # запросами на изменение родственников.
            await self.acquire_lock(conn, self.import_id)

            # Получаем информацию о жителе
            citizen = await self.get_citizen(conn, self.import_id,
                                             self.citizen_id)
            if not citizen:
                raise HTTPNotFound()

            # Обновляем таблицу citizens
            await self.update_citizen(conn, self.import_id, self.citizen_id,
                                      self.request['data'])

            # Обновляем родственные связи
            if 'relatives' in self.request['data']:
                cur_relatives = set(citizen['relatives'])
                new_relatives = set(self.request['data']['relatives'])
                await self.remove_relatives(
                    conn, self.import_id, self.citizen_id,
                    cur_relatives - new_relatives
                )
                await self.add_relatives(
                    conn, self.import_id, self.citizen_id,
                    new_relatives - cur_relatives
                )

            # Получаем актуальную информацию о
            citizen = await self.get_citizen(conn, self.import_id,
                                             self.citizen_id)
        return Response(body={'data': citizen})
