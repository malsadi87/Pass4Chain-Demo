from sawtooth_signing import Signer

from supply_chain_client.SupplyChainClient import SupplyChainClient

from supply_chain_client.crypto import get_new_signer
from supply_chain_client.models.agent import AgentItem
from supply_chain_client.models.fish_pallet import fish_pallet_type, create_fish_pallet, create_temperature


class ExampleClient(SupplyChainClient):

    def __init__(self, api_url: str, signer: Signer):
        super().__init__(api_url, signer)

    def add_pallet(self, agent: AgentItem, pallet_id: str, trip_id: int, specie_name: str):
        pallet_item = create_fish_pallet(pallet_id, trip_id, specie_name)
        return self.add(agent, pallet_item)

    def update_temperature(self, agent: AgentItem, record_id: str, temperature: int, location: [int, int]):
        temperature_property = create_temperature(temperature, location)
        return self.update_record(agent, record_id, [temperature_property])


if __name__ == "__main__":

    client_signer = get_new_signer()  # Pass in private key here if a persistent signer is needed.
    client = ExampleClient("http://localhost:8008", client_signer)
    test_agent = AgentItem("agent0001")  # Pass in Signer here if a persistent agent is needed.

    client.add_agent(test_agent)
    client.add_record_type(test_agent, fish_pallet_type)
    client.add_pallet(test_agent, "p1", 2, "Cod")
    client.update_temperature(test_agent, "p1", 11, [69, 12])
    client.update_temperature(test_agent, "p1", 12, [70, 12])

    print(client.get_agent(test_agent.public_key))
    print(client.get_record("p1"))
    print(client.get_property("p1", "Specie"))
    print(client.get_property("p1", "Temperature"))
    print(client.get_property_page("p1", "Temperature", 1))
