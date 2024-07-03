from datetime import datetime
import os
from .file_handler import FileHandler
from io import BufferedReader
import json
from llm.llmstrategy import LLMStrategy
from jsonschema import validate, ValidationError
from pypdf import PdfReader
from pdf2image import convert_from_path, convert_from_bytes
from typing import List
from utils import encode_image

TMP_DIR = "tmp"

class ImageHandler(FileHandler):
    def __init__(self, llm_strategy: LLMStrategy, max_retry: int = 3) -> None:
        super().__init__(llm_strategy, max_retry)
        if not os.path.exists(TMP_DIR):
            os.makedirs(TMP_DIR)

    def process_file(self, file_path: str) -> dict:
        return self.process_file_with_custom_prompt(file_path, self.default_prompt)

    def process_files(self, file_path: List[str]) -> dict:
        return self.process_files_with_custom_prompt(file_path, self.default_prompt)

    def process_file_with_custom_prompt(self, file_path: str, prompt: str) -> dict:
        return self.process_files_with_custom_prompt([file_path], prompt)

    def process_files_with_custom_prompt(self, file_paths: List[str], prompt: str) -> dict:
        base64_images = []
        for image_path in file_paths:
            b64 = encode_image(image_path)
            base64_images.append(b64)

        response = self.strip_md(self.llm_strategy.generate_response_with_images(prompt, base64_images))
        print(response)
        if not self.valid_response(response):
            i = 1
            while i < self.max_retry:
                print("LLM gave invalid response, retrying...")
                response = self.strip_md(self.llm_strategy.generate_response_with_images(prompt, base64_images))
                print(response)
                if self.valid_response(response):
                    break
                i += 1

        if self.valid_response(response):
            return json.loads(response)
        else:
            return {}
