import azure.functions as func
import logging
from multipart import MultipartParser
import io
import cgi
import os
from dotenv import load_dotenv
load_dotenv()

def parse_multipart_form_data(req: func.HttpRequest) -> dict:
    # Extract the boundary from the content type header
    content_type_header = req.headers.get('content-type')
    _, params = cgi.parse_header(content_type_header)
    boundary = params['boundary']

    # Use the boundary to parse the request body
    parser = MultipartParser(stream=io.BytesIO(req.get_body()), boundary=boundary)
    
    # Extract parts
    files = {}
    for part in parser.parts():
        # Assuming part has filename attribute to consider it as file
        if part.filename:
            # You can save the file here or process it as needed
            files[part.name] = (part.filename, part.content)
    return files

def get_env_var(name: str) -> str:
    return os.getenv(name)