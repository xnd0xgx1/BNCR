from abc import ABC, abstractmethod

class AOIInterface(ABC):
    @abstractmethod
    def Call(self, content):
        pass
    @abstractmethod
    def clean_json_string(self,s):
        pass
   
   