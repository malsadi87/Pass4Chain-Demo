import enum
import hashlib

"""
https://sawtooth.hyperledger.org/docs/core/releases/latest/app_developers_guide/address_and_namespace.html
An address begins with a namespace prefix of six hex characters representing three bytes. The rest of the address, 
    32 bytes represented as 64 hex characters, can be calculated in various ways.
    However, certain guidelines should be followed when creating addresses, and specific requirements must be met.

The address must be deterministic: that is, any validator or client that needs to calculate the address must be able to
 calculate the same address, every time, when given the same input
"""

FAMILY_NAME: str = 'paasforchain_adresser'
FAMILY_VERSION: str = '0.01'

# The namespace prefix consists of six hex characters, or three bytes
NAMESPACE: str = hashlib.sha512(FAMILY_NAME.encode('utf-8')).hexdigest()[:6]
AGENT_PREFIX: str = 'ae'
RECORD_PREFIX: str = 'ec'
PROPERTY_PREFIX: str = 'ea'
PROPOSAL_PREFIX: str = 'aa'
RECORD_TYPE_PREFIX: str = 'ee'

RECORD_TYPE_ADDRESS_RANGE = NAMESPACE + RECORD_TYPE_PREFIX

def _hash(identifier: str) -> str:
    return hashlib.sha512(identifier.encode()).hexdigest()


@enum.unique
class AddressSpace(enum.IntEnum):
    AGENT: int = 0
    RECORD: int = 1
    PROPERTY: int = 2
    PROPOSAL: int = 3
    RECORD_TYPE: int = 4
    PROPERTY_PAGE: int = 5

    OTHER_FAMILY: int = 100


def get_agent_address(public_key: str) -> str:
    return NAMESPACE + AGENT_PREFIX + hashlib.sha512(
        public_key.encode('utf-8')).hexdigest()[:62]


def get_record_address(record_id: str) -> str:
    return NAMESPACE + RECORD_PREFIX + hashlib.sha512(
        record_id.encode('utf-8')).hexdigest()[:62]


def get_record_type_address(type_name: str) -> str:
    return NAMESPACE + RECORD_TYPE_PREFIX + hashlib.sha512(
        type_name.encode('utf-8')).hexdigest()[:62]


def get_property_address(record_id: str, property_name: str, page: int = 0) -> str:
    return make_property_address_range(record_id) + _hash(property_name)[:22] + num_to_page_number(page)


def num_to_page_number(record_id) -> str:
    return '{0:0{1}x}'.format(int(record_id), 4)


def make_property_address_range(record_id) -> str:
    return NAMESPACE + PROPERTY_PREFIX + _hash(record_id)[:36]


def make_proposal_address(record_id, agent_id) -> str:
    return NAMESPACE + PROPOSAL_PREFIX + _hash(record_id)[:36] + _hash(agent_id)[:26]


def get_address_type(address) -> int:
    if address[:len(NAMESPACE)] != NAMESPACE:
        return AddressSpace.OTHER_FAMILY

    infix = address[6:8]

    if infix == AGENT_PREFIX:
        return AddressSpace.AGENT
    if infix == RECORD_PREFIX:
        return AddressSpace.RECORD
    if infix == PROPERTY_PREFIX:
        if address[-4:] == "0000":
            return AddressSpace.PROPERTY
        else:
            return AddressSpace.PROPERTY_PAGE
    if infix == PROPOSAL_PREFIX:
        return AddressSpace.PROPOSAL
    if infix == RECORD_TYPE_PREFIX:
        return AddressSpace.RECORD_TYPE
    return AddressSpace.OTHER_FAMILY
