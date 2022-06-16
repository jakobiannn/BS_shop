"""
Модуль содержит схемы для валидации данных в запросах и ответах.

Схемы валидации запросов используются в бою для валидации данных отправленных
клиентами.

Схемы валидации ответов *ResponseSchema используются только при тестировании,
чтобы убедиться что обработчики возвращают данные в корректном формате.
"""
from datetime import date

from marshmallow import Schema, ValidationError, validates, validates_schema
from marshmallow.fields import Date, Dict, Float, Int, List, Nested, Str
from marshmallow.validate import Length, OneOf, Range

from shop.db.schema import UnitType

DATE_FORMAT = '%Y-%m-%dT%H:%M:%S.%f%z'


class PatchShopUnitSchema(Schema):
    name = Str(validate=Length(min=1, max=256))
    type = Str(validate=OneOf([type.value for type in UnitType]))
    date = Date(format=DATE_FORMAT)

    @validates('date')
    def validate_birth_date(self, value: date):
        if value > date.today():
            raise ValidationError("Registration date can't be in future")


class ShopUnitSchema(PatchShopUnitSchema):
    unit_id = Int(validate=Range(min=0), strict=True, required=True)
    name = Str(validate=Length(min=1, max=256), required=True)
    type = Str(validate=OneOf([type.value for type in UnitType]),
               required=True)
    date = Date(format=DATE_FORMAT, required=True)
    town = Str(validate=Length(min=1, max=256), required=True)
    street = Str(validate=Length(min=1, max=256), required=True)
    building = Str(validate=Length(min=1, max=256), required=True)
    apartment = Int(validate=Range(min=0), strict=True, required=True)
    relatives = List(Int(validate=Range(min=0), strict=True), required=True)


class ImportSchema(Schema):
    citizens = Nested(ShopUnitSchema, many=True, required=True,
                      validate=Length(max=10000))

    @validates_schema
    def validate_unique_citizen_id(self, data, **_):
        citizen_ids = set()
        for citizen in data['citizens']:
            if citizen['unit_id'] in citizen_ids:
                raise ValidationError(
                    'unit_id %r is not unique' % citizen['unit_id']
                )
            citizen_ids.add(citizen['unit_id'])


class ImportIdSchema(Schema):
    import_id = Int(strict=True, required=True)


class ImportResponseSchema(Schema):
    data = Nested(ImportIdSchema(), required=True)


class CitizensResponseSchema(Schema):
    data = Nested(ShopUnitSchema(many=True), required=True)


class PatchCitizenResponseSchema(Schema):
    data = Nested(ShopUnitSchema(), required=True)


class ErrorSchema(Schema):
    code = Str(required=True)
    message = Str(required=True)
    fields = Dict()


class ErrorResponseSchema(Schema):
    error = Nested(ErrorSchema(), required=True)
