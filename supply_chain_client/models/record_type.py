import time
from typing import List

from protobuf.property_pb2 import PropertySchema
from protobuf.payload_pb2 import CreateRecordTypeAction, SupplyChainPayload
from addressing.supply_chain_addressers.addresser import get_record_type_address
from supply_chain_client.models.item import BlockchainItem


class RecordTypeItem(BlockchainItem):

    def __init__(self, name: str, properties: List[PropertySchema]):
        self.name = name
        self.properties = properties

    @property
    def creation_payload(self):
        action = CreateRecordTypeAction(name=self.name)
        action.properties.extend(self.properties)
        return SupplyChainPayload(
            action=SupplyChainPayload.Action.CREATE_RECORD_TYPE,
            timestamp=int(time.time()),
            create_record_type=action
        ).SerializeToString()

    @property
    def creation_addresses(self):
        return [self.address]

    @property
    def address(self):
        return get_record_type_address(self.name)
