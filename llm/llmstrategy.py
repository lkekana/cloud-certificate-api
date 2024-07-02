from abc import ABC, abstractmethod
from io import BufferedReader

class LLMStrategy(ABC):
    @abstractmethod
    def generate_response(self, prompt: str) -> str:
        pass
    
    @abstractmethod
    def generate_response_from_file(self, file_buffer: BufferedReader) -> str:
        pass