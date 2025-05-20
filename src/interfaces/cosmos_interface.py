from abc import ABC, abstractmethod

class CosmosInterface(ABC):
    @abstractmethod
    def save_record(self, record):
        pass
    @abstractmethod
    def get_latest_by_field(self, field_name,field_value):
        pass


   