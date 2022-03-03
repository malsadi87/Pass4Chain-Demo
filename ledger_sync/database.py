# file is modified from original
# Copyright 2017 Intel Corporation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# -----------------------------------------------------------------------------

from ledger_sync.config import DB_HOST, DB_PORT, DB_NAME

import logging
from rethinkdb import RethinkDB
r = RethinkDB()

LOGGER = logging.getLogger(__name__)


class Database(object):
    """Simple object for managing a connection to a rethink database
    """
    def __init__(self):
        self._name = DB_NAME
        self._conn = None

    def connect(self):
        """Initializes a connection to the database and ensures that the required db and tables exist
        """
        LOGGER.debug('Connecting to database: %s:%s', DB_HOST, DB_PORT)
        self._conn = r.connect(host=DB_HOST, port=DB_PORT)
        self._ensure_db_and_tables()

    def disconnect(self):
        """Closes the connection to the database
        """
        LOGGER.debug('Disconnecting from database')
        self._conn.close()

    def _ensure_db_and_tables(self):
        """ Ensures that the necessary tables exists
        """
        dbs = r.db_list().run(self._conn)
        if DB_NAME not in dbs:
            r.db_create(DB_NAME).run(self._conn)

        self._conn.use('supply_chain')

        tables = r.table_list().run(self._conn)
        if 'blocks' not in tables:
            r.table_create("blocks", primary_key="block_num").run(self._conn)
        if 'agents' not in tables:
            r.table_create("agents").run(self._conn)
            r.db(self._name).table('agents').index_create("public_key").run(self._conn)
        if 'recordTypes' not in tables:
            r.table_create("recordTypes").run(self._conn)
            r.db(self._name).table('recordTypes').index_create("name").run(self._conn)
        if 'records' not in tables:
            r.table_create("records").run(self._conn)
            r.db(self._name).table('records').index_create("record_id").run(self._conn)
        if 'properties' not in tables:
            r.table_create("properties").run(self._conn)
            r.db(self._name).table('properties')\
                .index_create('attributes', [r.row["name"], r.row["record_id"]]).run(self._conn)
        if 'propertyPages' not in tables:
            r.table_create("propertyPages").run(self._conn)
            r.db(self._name).table('propertyPages')\
                .index_create('attributes', [r.row["name"], r.row["record_id"], r.row["page_num"]]).run(self._conn)

    def fetch(self, table_name, primary_id):
        """Fetches a single resource by its primary id
        """
        return r.db(self._name).table(table_name)\
            .get(primary_id).run(self._conn)

    def insert(self, table_name, docs):
        """Inserts a document or a list of documents into the specified table
        in the database
        """
        return r.db(self._name).table(table_name).insert(docs).run(self._conn)

    def last_known_blocks(self, count):
        """Fetches the ids of the specified number of most recent blocks
        """
        cursor = r.db(self._name).table('blocks')\
            .order_by('block_num')\
            .get_field('block_id')\
            .run(self._conn)

        return list(cursor)[-count:]

    def drop_fork(self, block_num):
        """Deletes all resources from a particular block_num
        """
        block_results = r.db(self._name).table('blocks')\
            .filter(lambda rsc: rsc['block_num'].ge(block_num))\
            .delete()\
            .run(self._conn)

        resource_results = r.db(self._name).table_list()\
            .for_each(
                lambda table_name: r.branch(
                    r.eq(table_name, 'blocks'),
                    [],
                    r.eq(table_name, 'auth'),  # todo: figure out how we want to do auth
                    [],
                    r.db(self._name).table(table_name)
                    .filter(lambda rsc: rsc['start_block_num'].ge(block_num))
                    .delete()))\
            .run(self._conn)

        return {k: v + resource_results[k] for k, v in block_results.items()}

    def get_table(self, table_name):
        """Returns a rethink table query, which can be added to, and
        eventually run with run_query
        """
        return r.db(self._name).table(table_name)

    def run_query(self, query):
        """Takes a query based on get_table, and runs it.
        """
        return query.run(self._conn)
