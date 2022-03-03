from abc import ABC, abstractmethod


class BlockchainItem(ABC):

    @property
    @abstractmethod
    def creation_payload(self):
        pass

    @property
    @abstractmethod
    def creation_addresses(self):
        pass

    @property
    @abstractmethod
    def address(self):
        pass
