from sqlalchemy import select

from shop.db.schema import units_table

CITIZENS_QUERY = select([
    units_table.c.unit_id,
    units_table.c.name,
    units_table.c.date,
    units_table.c.type,
    units_table.c.town,
    units_table.c.street,
    units_table.c.building,
    units_table.c.apartment,
]).group_by(
    units_table.c.import_id,
    units_table.c.unit_id
)
