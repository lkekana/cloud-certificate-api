from abc import ABC, abstractmethod
from io import BufferedReader
from typing import List

class LLMStrategy(ABC):
    @abstractmethod
    def generate_response(self, prompt: str) -> str:
        pass

    @abstractmethod
    def generate_response_with_images(self, prompt: str, base64_images: List[str]) -> str:
        pass

    @abstractmethod
    def generate_response_with_file(self, prompt: str, file_buffer: BufferedReader) -> str:
        pass