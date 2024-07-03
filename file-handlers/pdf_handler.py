from datetime import datetime
import os
from .file_handler import FileHandler
from io import BufferedReader
import json
from ..llm.llmstrategy import LLMStrategy
from jsonschema import validate, ValidationError
from pypdf import PdfReader
from pdf2image import convert_from_path, convert_from_bytes
from typing import List
from utils import encode_image

TMP_DIR = "tmp"

class PDFHandler(FileHandler):
    def __init__(self, llm_strategy: LLMStrategy, max_retry: int = 3) -> None:
        super().__init__(llm_strategy, max_retry)
        if not os.path.exists(TMP_DIR):
            os.makedirs(TMP_DIR)


    def process_file(self, file_buffer: BufferedReader) -> dict:
        if not self.is_pdf_scan(file_buffer):
            return self.process_file_with_custom_prompt(file_buffer, self.default_prompt)
        else:
            return self.process_pdf_with_images(file_buffer, self.default_prompt)

    def process_file_with_custom_prompt(self, file_buffer: BufferedReader, prompt: str) -> dict:
        if not self.is_pdf_scan(file_buffer):
            response = self.llm_strategy.generate_response(prompt)
            if not self.valid_response(response):
                i = 1
                while i < self.max_retry:
                    response = self.llm_strategy.generate_response(prompt)
                    if self.valid_response(response):
                        break
                    i += 1

            if self.valid_response(response):
                return json.loads(response)
            else:
                return {}
        else:
            return self.process_pdf_with_images(file_buffer, prompt)

    def process_pdf_with_images(self, file_buffer: BufferedReader, prompt: str) -> dict:
        image_paths = self.get_images_from_pdf(file_buffer)
        base64_images = []
        for image_path in image_paths:
            b64 = encode_image(image_path)
            base64_images.append(b64)

        response = self.llm_strategy.generate_response_with_images(prompt, base64_images)
        if not self.valid_response(response):
            i = 1
            while i < self.max_retry:
                response = self.llm_strategy.generate_response_with_images(prompt, base64_images)
                if self.valid_response(response):
                    break
                i += 1

        if self.valid_response(response):
            # delete generated images
            for image_path in image_paths:
                os.remove(image_path)
            return json.loads(response)
        else:
            return {}

    def is_pdf_scan(self, file_buffer: BufferedReader) -> bool:
        read_pdf = PdfReader(file_buffer)
        number_of_pages = read_pdf.get_num_pages()
        print("pdf has", number_of_pages, "pages")
        file_content = ""
        for i in range(number_of_pages):
            page = read_pdf.pages[i]
            page_content = page.extract_text()
            file_content += page_content
        print(len(file_content))
        print(file_content)
        if len(file_content) > 0:
            return False

        return True

    def get_images_from_pdf(self, file_buffer: BufferedReader, image_prefix: str = datetime.now().strftime("%Y%m%d%H%M%S")) -> List[str]:
        images = convert_from_bytes(file_buffer.read())
        image_paths = []

        for i, image in enumerate(images):
            image_path = f"{image_prefix}_page_{i}.png"
            image_path = os.path.join(TMP_DIR, image_path)
            image.save(image_path, "PNG")
            image_paths.append(image_path)
        return image_paths
