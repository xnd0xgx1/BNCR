from abc import ABC, abstractmethod

class DocIntInterface(ABC):
    @abstractmethod
    def Process(self, filestream):
        pass

   