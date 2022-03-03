from fastapi import HTTPException
from rethinkdb.errors import ReqlNonExistenceError

from db_config import DB_HOST, DB_PORT, DB_NAME

from rethinkdb import RethinkDB

from models import VALUES_LOOKUP, ReportedValue

r = RethinkDB()
r.set_loop_type('asyncio')


async def get_table_feed(table_name: str):
    connection = await _get_connection()
    return await r.table(table_name).changes().run(connection)


async def _get_connection():
    return await r.connect(host=DB_HOST, port=DB_PORT, db=DB_NAME)


class Database:

    def __init__(self):
        self.connection = None

    async def connect(self):
        self.connection = await _get_connection()

    async def get_agents(self):
        block = await self._current_block_num()
        return await r.table('agents') \
            .filter((r.row['start_block_num'] <= block) & (r.row['end_block_num'] >= block)) \
            .without('delta_id', 'start_block_num', 'end_block_num') \
            .coerce_to('array').run(self.connection)

    async def get_record_types(self):
        block = await self._current_block_num()
        return await r.table('recordTypes') \
            .filter((r.row['start_block_num'] <= block) & (r.row['end_block_num'] >= block)) \
            .without('delta_id', 'start_block_num', 'end_block_num') \
            .coerce_to('array').run(self.connection)

    async def get_records(self):
        block = await self._current_block_num()
        return await r.table('records') \
            .filter((r.row['start_block_num'] <= block) & (r.row['end_block_num'] >= block)) \
            .without('delta_id', 'start_block_num', 'end_block_num') \
            .coerce_to('array').run(self.connection)

    async def get_properties(self, record_id: str):
        block = await self._current_block_num()
        return await r.table('properties') \
            .filter({'record_id': record_id}) \
            .filter((r.row['start_block_num'] <= block) & (r.row['end_block_num'] >= block)) \
            .without('delta_id', 'start_block_num', 'end_block_num') \
            .coerce_to('array').run(self.connection)

    async def get_property(self, record_id: str, property_name: str):
        block = await self._current_block_num()
        prop = await r.table('properties') \
            .filter({'name': property_name, 'record_id': record_id}) \
            .filter((r.row['start_block_num'] <= block) & (r.row['end_block_num'] >= block)) \
            .max('start_block_num') \
            .without('delta_id', 'start_block_num', 'end_block_num') \
            .run(self.connection)

        try:
            return prop
        except IndexError:
            raise HTTPException(
                status_code=404, detail=f'Property ({property_name}) or record_id ({record_id}) not found.')

    async def get_property_type(self, record_id: str, property_name: str):
        prop = await self.get_property(record_id, property_name)
        return prop["data_type"]

    async def get_property_page(self, record_id, property_name, page_num=1):
        property_dtype = await self.get_property_type(record_id, property_name)
        value_key = VALUES_LOOKUP[property_dtype]
        excludes = {'reported_values': {v: True for v in VALUES_LOOKUP.values()}}
        excludes['reported_values'].pop(value_key)

        block = await self._current_block_num()

        resp = await r.table('propertyPages') \
            .filter({
                'record_id': record_id,
                'name': property_name,
                'page_num': page_num
            }) \
            .filter((r.row['start_block_num'] <= block) & (r.row['end_block_num'] >= block)) \
            .max('start_block_num') \
            .without('delta_id', 'start_block_num', 'end_block_num') \
            .without(excludes) \
            .coerce_to('array') \
            .run(self.connection)

        try:
            return resp
        except IndexError:
            raise HTTPException(status_code=404, detail=f"Page {page_num} not found.")

    async def _current_block_num(self):
        try:
            block = await r.table('blocks') \
                .max('block_num') \
                .without('block_id') \
                .run(self.connection)
            return block['block_num']
        except ReqlNonExistenceError:
            raise HTTPException(
                status_code=404,
                detail=f"Failed to find a block in database. Has any state been added to the blocckchain yet?")
        except IndexError:
            raise HTTPException(status_code=500, detail=f"Failed to find a block in database.")

