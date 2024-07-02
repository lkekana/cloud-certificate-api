from abc import ABC, abstractmethod

class LLMStrategy(ABC):
    @abstractmethod
    def generate_response(self, prompt: str) -> str:
        pass