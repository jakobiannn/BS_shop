from enum import Enum, unique
from alembic import op
from sqlalchemy import (
    Column, Date, Enum as PgEnum, ForeignKey, ForeignKeyConstraint, Integer,
    MetaData, String, Table,
)

# SQLAlchemy рекомендует использовать единый формат для генерации названий для
# индексов и внешних ключей.
# https://docs.sqlalchemy.org/en/13/core/constraints.html#configuring-constraint-naming-conventions
convention = {
    'all_column_names': lambda constraint, table: '_'.join([
        column.name for column in constraint.columns.values()
    ]),
    'ix': 'ix__%(table_name)s__%(all_column_names)s',
    'uq': 'uq__%(table_name)s__%(all_column_names)s',
    'ck': 'ck__%(table_name)s__%(constraint_name)s',
    'fk': 'fk__%(table_name)s__%(all_column_names)s__%(referred_table_name)s',
    'pk': 'pk__%(table_name)s'
}

metadata = MetaData(naming_convention=convention)


@unique
class UnitType(Enum):
    offer = 'offer'
    category = 'category'


imports_table = Table(
    'imports',
    metadata,
    Column('import_id', Integer, primary_key=True)
)

units_table = Table(
    'units',
    metadata,
    Column('import_id', Integer, ForeignKey('imports.import_id'),
           primary_key=True),
    Column('unit_id', Integer, primary_key=True),
    Column('name', String, nullable=False),
    Column('date', Date, nullable=False),
    Column('type', PgEnum(UnitType, name='type'), nullable=False),
)
