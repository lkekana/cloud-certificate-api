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

class PDFHandler(FileHandler):
    def __init__(self, llm_strategy: LLMStrategy, max_retry: int = 3) -> None:
        super().__init__(llm_strategy, max_retry)
        if not os.path.exists(TMP_DIR):
            os.makedirs(TMP_DIR)


    def process_file(self, file_path: str) -> dict:
        file_buffer = open(file_path, "rb")
        if not self.is_pdf_scan(file_buffer):
            file_buffer.close()
            return self.process_file_with_custom_prompt(file_path, self.default_prompt)
        else:
            file_buffer.close()
            return self.process_pdf_with_images(file_path, self.default_prompt)

    def process_file_with_custom_prompt(self, file_path: str, prompt: str) -> dict:
        file_buffer = open(file_path, "rb")
        if not self.is_pdf_scan(file_buffer):
            response = self.strip_md(self.llm_strategy.generate_response_with_file(file_buffer))
            print(response)
            if not self.valid_response(response):
                i = 1
                while i < self.max_retry:
                    print("LLM gave invalid response, retrying...")
                    file_buffer.seek(0)
                    response = self.strip_md(self.llm_strategy.generate_response_with_file(file_buffer))
                    print(response)
                    if self.valid_response(response):
                        break
                    i += 1
            file_buffer.close()
            if self.valid_response(response):
                return json.loads(response)
            else:
                return {}
        else:
            resp = self.process_pdf_with_images(file_buffer, prompt)
            file_buffer.close()
            return resp

    def process_pdf_with_images(self, file_buffer: BufferedReader, prompt: str) -> dict:
        image_paths = self.get_images_from_pdf(file_buffer)
        base64_images = []
        for image_path in image_paths:
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

        # delete generated images
        for image_path in image_paths:
            os.remove(image_path)

        if self.valid_response(response):
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
        print("length of file content:", len(file_content))
        print("file content:", file_content)
        if len(file_content) > 0:
            return False
        return True

    def get_images_from_pdf(self, file_path: str, image_prefix: str = datetime.now().strftime("%Y%m%d%H%M%S")) -> List[str]:
        images = convert_from_path(file_path)
        image_paths = []

        for i, image in enumerate(images):
            image_path = f"{image_prefix}_page_{i}.png"
            image_path = os.path.join(TMP_DIR, image_path)
            image.save(image_path, "PNG")
            image_paths.append(image_path)
        return image_paths
