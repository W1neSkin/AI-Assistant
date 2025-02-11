from abc import ABC, abstractmethod

class BaseLLM(ABC):
    @abstractmethod
    async def initialize(self):
        pass
        
    @abstractmethod
    async def generate_answer(self, prompt: str) -> str:
        pass 