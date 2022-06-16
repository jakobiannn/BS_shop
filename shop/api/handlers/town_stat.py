from http import HTTPStatus

from aiohttp.web_response import Response
from aiohttp_apispec import docs, response_schema
from sqlalchemy import func, select, text

from shop.api.schema import TownAgeStatResponseSchema
from shop.db.schema import units_table
from shop.utils.pg import rounded

from .base import BaseImportView


class TownAgeStatView(BaseImportView):
    URL_PATH = r'/imports/{import_id:\d+}/towns/stat/percentile/age'
    CURRENT_DATE = text("TIMEZONE('utc', CURRENT_TIMESTAMP)")

    @docs(summary='Статистика возрастов жителей по городам')
    @response_schema(TownAgeStatResponseSchema(), code=HTTPStatus.OK.value)
    async def get(self):
        await self.check_import_exists()

        age = func.age(self.CURRENT_DATE, units_table.c.date)
        age = func.date_part('year', age)
        query = select([
            units_table.c.town,
            rounded(func.percentile_cont(0.5).within_group(age)).label('p50'),
            rounded(func.percentile_cont(0.75).within_group(age)).label('p75'),
            rounded(func.percentile_cont(0.99).within_group(age)).label('p99')
        ]).select_from(
            units_table
        ).group_by(
            units_table.c.town
        ).where(
            units_table.c.import_id == self.import_id
        )

        stats = await self.pg.fetch(query)
        return Response(body={'data': stats})
