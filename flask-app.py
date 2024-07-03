from flask import Flask, request, jsonify, make_response
import os
import json
import datetime
import logging
from file import hello_world
from utils import parse_multipart_form_data
import traceback
from llm.openai import *
from file_handlers.pdf_handler import PDFHandler
from file_handlers.image_handler import ImageHandler

app = Flask(__name__)
strategy = GPT4oStrategy()
pdf_handler = PDFHandler(strategy)
image_handler = ImageHandler(strategy)
TMP_DIR = "tmp"
if not os.path.exists(TMP_DIR):
    os.makedirs(TMP_DIR)

@app.route('/upload', methods=['POST'])
def upload():
    content_type = request.headers.get('Content-Type')
    if 'multipart/form-data' in content_type:
        try:
            files = request.files
            responses = []
            for file_name in files:
                file = files[file_name]
                path = os.path.join(TMP_DIR, file.filename)
                file.save(path)

                if '.pdf' in file.filename:
                    response = pdf_handler.process_file(path)
                    responses.append(response)
                elif any(ext in file.filename for ext in ['.png', '.jpeg', '.jpg', '.webp', '.gif']):
                    response = image_handler.process_file(path)
                    responses.append(response)
                else:
                    responses.append({})

                os.remove(path)
            return jsonify(responses)
        except Exception as e:
            logging.error(f"Error processing multipart form data: {e}")
            return make_response(jsonify(error="Error processing multipart form data"), 500)
    elif 'application/json' in content_type:
        return jsonify(request.get_json())
    elif 'application/pdf' in content_type:
        filename = request.headers.get('filename')
        time = datetime.datetime.now().strftime("%Y%m%d%H%M%S%f")
        if not filename:
            filename = f"{time}.pdf"
        path = os.path.join(TMP_DIR, filename)
        with open(path, "wb") as f:
            f.write(request.data)
        response = pdf_handler.process_file(path)
        os.remove(path)
        return jsonify(response)
    else:
        return make_response(jsonify(error="This endpoint only accepts application/json and application/pdf"), 400)

if __name__ == '__main__':
    app.run(debug=True)