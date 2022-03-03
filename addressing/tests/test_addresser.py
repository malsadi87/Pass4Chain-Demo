import unittest
from uuid import uuid4

from addressing.supply_chain_addressers import addresser


class AddresserTest(unittest.TestCase):

    def test_agent_address(self):
        agent_address = addresser.get_agent_address(uuid4().hex)

        self.assertEqual(len(agent_address), 70, "The agent address is valid.")

        self.assertEqual(addresser.get_address_type(agent_address),
                         addresser.AddressSpace.AGENT,
                         "The address is correctly identified as an Agent.")

    def test_record_address(self):
        offer_address = addresser.get_record_address(uuid4().hex)

        self.assertEqual(len(offer_address), 70, "The address is valid.")

        self.assertEqual(addresser.get_address_type(offer_address),
                         addresser.AddressSpace.RECORD,
                         "The address is correctly identified as an Record.")

    def test_property_address(self):
        property_name = uuid4().hex
        record_address = addresser.get_record_address(uuid4().hex)
        property_address = addresser.make_property_address(record_address, property_name, 0)

        self.assertEqual(len(property_address), 70, "The address is valid.")

        self.assertEqual(addresser.get_address_type(property_address),
                         addresser.AddressSpace.PROPERTY,
                         "The address is correctly identified as an PROPERTY.")

    def test_proposal_address(self):
        agent_address = addresser.get_agent_address(uuid4().hex)
        record_address = addresser.get_record_address(uuid4().hex)
        proposal_address = addresser.make_proposal_address(record_address, agent_address)

        self.assertEqual(len(proposal_address), 70, "The address is valid.")

        self.assertEqual(addresser.get_address_type(proposal_address),
                         addresser.AddressSpace.PROPOSAL,
                         "The address is correctly identified as an PROPOSAL.")

    def test_record_type_address(self):
        record_type = addresser.get_record_type_address(uuid4().hex)

        self.assertEqual(len(record_type), 70, "The address is valid.")

        self.assertEqual(addresser.get_address_type(record_type),
                         addresser.AddressSpace.RECORD_TYPE,
                         "The address is correctly identified as an Record type.")
