from abc import ABC, abstractmethod

class STInterface(ABC):
    @abstractmethod
    def Save(self, content):
        pass
    @abstractmethod
    def Get(self,document_name):
        pass
   
   