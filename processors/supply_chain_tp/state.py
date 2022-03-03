from protobuf.supply_chain_protos import agent_pb2

# TODO: Populate me
from addressing.supply_chain_addressers import addresser


class SupplyChainState(object):
    def __init__(self, context, timeout=2):
        self._context = context
        self._timeout = timeout

    def get_agent(self, public_key):
        """Gets the agent associated with the public_key

        Args:
            public_key (str): The public key of the agent

        Returns:
            agent_pb2.Agent: Agent with the provided public_key
        """
        address = addresser.get_agent_address(public_key)
        state_entries = self._context.get_state(
            addresses=[address], timeout=self._timeout)
        if state_entries:
            container = agent_pb2.AgentContainer()
            container.ParseFromString(state_entries[0].data)
            for agent in container.entries:
                if agent.public_key == public_key:
                    return agent

        return None

    def set_agent(self, payload, signer, timestamp):
        """Creates a new agent in state

        Args:
            # public_key (str): The public key of the agent
            # name (str): The human-readable name of the agent
            timestamp (int): Unix UTC timestamp of when the agent was created
        """
        print("Hello?")
        address = addresser.get_agent_address(signer)
        agent = agent_pb2.Agent(
            public_key=signer, name=payload.name, timestamp=timestamp)
        container = agent_pb2.AgentContainer()
        state_entries = self._context.get_state(
            addresses=[address], timeout=self._timeout)
        if state_entries:
            container.ParseFromString(state_entries[0].data)

        container.entries.extend([agent])
        data = container.SerializeToString()

        updated_state = {address: data}
        self._context.set_state(updated_state, timeout=self._timeout)

#     def set_agent_old(self, public_key, name, timestamp):
#
#         address = addresser.get_agent_address(public_key)
#         agent = agent_pb2.Agent(
#             public_key=public_key, name=name, timestamp=timestamp)
#         container = agent_pb2.AgentContainer()
#         state_entries = self._context.get_state(
#             addresses=[address], timeout=self._timeout)
#         if state_entries:
#             container.ParseFromString(state_entries[0].data)
#
#         container.entries.extend([agent])
#         data = container.SerializeToString()
#
#         updated_state = {address: data}
#         self._context.set_state(updated_state, timeout=self._timeout)
