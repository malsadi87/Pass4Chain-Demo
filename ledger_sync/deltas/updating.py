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

import sys

from addressing.supply_chain_addressers.addresser import get_address_type, AddressSpace


TABLE_NAMES = {
    AddressSpace.AGENT: 'agents',
    AddressSpace.RECORD_TYPE: 'recordTypes',
    AddressSpace.RECORD: 'records',
    AddressSpace.PROPERTY: 'properties',
    AddressSpace.PROPERTY_PAGE: 'propertyPages'
}

SECONDARY_INDEXES = {
    AddressSpace.AGENT: 'public_key',
    AddressSpace.RECORD_TYPE: 'name',
    AddressSpace.RECORD: 'record_id',
    AddressSpace.PROPERTY: 'attributes',
    AddressSpace.PROPERTY_PAGE: 'attributes'
}

SECONDARY_INDEX_COMPONENTS = {
    AddressSpace.AGENT: ['public_key'],
    AddressSpace.RECORD_TYPE: ['name'],
    AddressSpace.RECORD: ['record_id'],
    AddressSpace.PROPERTY: ['name', 'record_id'],
    AddressSpace.PROPERTY_PAGE: ['name', 'record_id', 'page_num']
}


def get_updater(database, block_num):
    """Returns an updater function, which can be used to update the database
    appropriately for a particular address/data combo.
    """
    return lambda adr, rsc: _update(database, block_num, adr, rsc)


def _update(database, block_num, address, resource):
    data_type = get_address_type(address)

    resource['start_block_num'] = block_num
    resource['end_block_num'] = sys.maxsize

    try:
        table_query = database.get_table(TABLE_NAMES[data_type])
        seconday_index = SECONDARY_INDEXES[data_type]
        index_components = SECONDARY_INDEX_COMPONENTS[data_type]
    except KeyError:
        raise TypeError('Unknown data type: {}'.format(data_type))

    components = [resource[c] for c in index_components]

    query = table_query\
        .get_all(components, index=seconday_index)\
        .filter({'end_block_num': sys.maxsize})\
        .update({'end_block_num': block_num})\
        .merge(table_query.insert(resource).without('replaced'))

    return database.run_query(query)
