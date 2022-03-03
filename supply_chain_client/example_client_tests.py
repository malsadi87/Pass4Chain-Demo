import unittest

from example_client import ExampleClient
from models.agent import AgentItem
from supply_chain_client.crypto import get_new_signer
from supply_chain_client.models.fish_pallet import fish_pallet_type

unittest.defaultTestLoader.sortTestMethodsUsing = lambda *args: -1

test_pallet = {
    "record_id": "test_pallet",
    "trip_id": 2,
    "Specie": "test_specie"
}


class ExampleClientMethodTests(unittest.TestCase):

    def setUp(self) -> None:
        signer = get_new_signer()
        self.client = ExampleClient("http://localhost:8008", signer)
        self.agent = AgentItem("test_agent")

    def test_client(self):
        """ Tests metohds for writing and reading state.
            Not in separate methods since reading is dependent on writing (might change this) """

        print("Writing state")

        # Test adding a new agent
        agent_response = self.client.add_agent(self.agent)
        self.assertEqual(agent_response, "COMMITTED")

        # Test adding an existing agent
        agent_response_inv = self.client.add_agent(self.agent)
        self.assertEqual(agent_response_inv, "INVALID")

        # Test adding fish pallet record type
        pallet_type_response = self.client.add_record_type(self.agent, fish_pallet_type)
        self.assertEqual(pallet_type_response, "COMMITTED")

        # Test adding existing fish pallet record type
        pallet_type_response_inv = self.client.add_record_type(self.agent, fish_pallet_type)
        self.assertEqual(pallet_type_response_inv, "INVALID")

        # Test adding a new pallet record
        pallet_response = self.client.add_pallet(
            self.agent, test_pallet["record_id"], test_pallet["trip_id"], test_pallet["Specie"])
        self.assertEqual(pallet_response, "COMMITTED")

        # Test adding an existing pallet record
        pallet_response_inv = self.client.add_pallet(
            self.agent, test_pallet["record_id"], test_pallet["trip_id"], test_pallet["Specie"])
        self.assertEqual(pallet_response_inv, "INVALID")

        # Test updating a property (Temperature w/location)
        temperature_response = self.client.update_temperature(self.agent, test_pallet["record_id"], 11, [70, 12])
        self.assertEqual(temperature_response, "COMMITTED")

        # Test updating a property (Temperature w/location) on non-existing record
        temperature_response_inv = self.client.update_temperature(self.agent, "not_test_pallet", 11, [69, 12])
        self.assertEqual(temperature_response_inv, "INVALID")

        print("Reading state")

        # Test getting an existing agent
        agent = self.client.get_agent(self.agent.public_key)
        self.assertEqual(agent.public_key, self.agent.public_key)
        self.assertEqual(agent.name, self.agent.name)

        # Test getting non-existing agent
        agent_inv = self.client.get_agent("not_a_real_public_key")
        self.assertEqual(agent_inv, None)

        # Test getting a record
        record = self.client.get_record(test_pallet["record_id"])
        self.assertEqual(record.record_id, test_pallet["record_id"])
        self.assertEqual(record.record_type, fish_pallet_type.name)

        # Test getting a non-existing record
        record_inv = self.client.get_record("not_a_real_record_id")
        self.assertEqual(record_inv, None)

        # Test getting a property
        prop = self.client.get_property(test_pallet["record_id"], "Specie")
        self.assertEqual(prop.name, "Specie")
        self.assertEqual(prop.record_id, test_pallet["record_id"])

        # Test getting a non-existing property on existing record
        property_inv = self.client.get_property(test_pallet["record_id"], "not_real_property")
        self.assertEqual(property_inv, None)

        # Test getting a property on non-existing record
        property_inv_2 = self.client.get_property("not_a_real_record_id", "Specie")
        self.assertEqual(property_inv_2, None)

        # Test getting a property page from non-exiting record
        property_page_inv = self.client.get_property_page("not_real_record_id", "Specie", 1)
        self.assertEqual(property_page_inv, None)

        # Test getting a property page from non-exiting property
        property_page_inv_2 = self.client.get_property_page(test_pallet["record_id"], "not_a_property", 1)
        self.assertEqual(property_page_inv_2, None)

        # Test getting a property page from non-exiting page
        property_page_inv_3 = self.client.get_property_page(test_pallet["record_id"], "Specie", 22)
        self.assertEqual(property_page_inv_3, None)

        # Test getting a property page
        property_page = self.client.get_property_page(test_pallet["record_id"], "Specie", 1)
        self.assertEqual(property_page.name, "Specie")
        self.assertEqual(property_page.record_id, test_pallet["record_id"])
        self.assertEqual(property_page.reported_values[0].string_value, test_pallet["Specie"])


if __name__ == '__main__':
    unittest.main()
