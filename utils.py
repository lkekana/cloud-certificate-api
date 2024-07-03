import base64
import azure.functions as func
import logging
from multipart import MultipartParser
from multipart.multipart import parse_options_header, parse_form
from multipart.multipart import Field, File
from multipart.multipart import FormParser
import io
import cgi
import os
from dotenv import load_dotenv
load_dotenv()
from pprint import pprint

def parse_multipart_form_data(req: func.HttpRequest) -> dict:
    # Extract the boundary from the content type header
    content_type_header = req.headers.get('content-type')
    content_type, params = parse_options_header(content_type_header)
    boundary = params.get(b'boundary')
    
    # Initialize storage for parsed data
    parsed_data = {"fields": {}, "files": {}}

    # Callbacks for handling parsed fields and files
    def on_field(field: Field):
        logging.info(f"Parsed field named {field.field_name} with value {field.value}")
        parsed_data["fields"][field.field_name] = field.value

    def on_file(file: File):
        # Assuming file content is stored in memory, for large files consider streaming to storage
        logging.info(f"Parsed file named {file.field_name} with filename {file.file_name}")
        f: io.BytesIO = file.file_object
        file_bytes = f.getvalue()
        length = len(file_bytes)
        print('file length:', length, len(file_bytes))
        print(f.getvalue()[0:10])
        # print(file.actual_file_name)
        # file.flush_to_disk()
        # print(file.actual_file_name)
        parsed_data["files"][file.file_name] = {"length": length, "content": file_bytes}

    # Create the parser with callbacks
    callbacks = {
        'on_field': on_field,
        'on_file': on_file,
    }
    
    print('content_type_header:', content_type_header)
    print('content_type:', content_type)
    print('boundary:', boundary)
    content_type_str = content_type.decode('utf-8')
    parser = FormParser(content_type_str, on_field, on_file, boundary=boundary)
    body = req.get_body()
    parser.write(body)
    return parsed_data

def get_env_var(name: str) -> str:
    return os.getenv(name)

def encode_image(image_path):
  with open(image_path, "rb") as image_file:
    return base64.b64encode(image_file.read()).decode('utf-8')

def print_pretty(data):
    pprint(data)