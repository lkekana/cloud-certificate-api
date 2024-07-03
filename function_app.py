import datetime
import json
import os
import azure.functions as func
import logging
from file import hello_world
from utils import parse_multipart_form_data
import traceback
from llm.openai import *
from file_handlers.pdf_handler import PDFHandler
from file_handlers.image_handler import ImageHandler


app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)
strategy = GPT4oStrategy()
pdf_handler = PDFHandler(strategy)
image_handler = ImageHandler(strategy)
TMP_DIR = "tmp"
if not os.path.exists(TMP_DIR):
    os.makedirs(TMP_DIR)

@app.route(route="HttpExample")
def HttpExample(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')
    # hello_world()
    name = req.params.get('name')
    print('params:', req.params)
    print('param name:', name)
    if not name:
        try:
            req_body = req.get_json()
        except ValueError:
            pass
        else:
            name = req_body.get('name')

    if name:
        return func.HttpResponse(f"Hello, {name}. This HTTP triggered function executed successfully.")
    else:
        return func.HttpResponse(
             "This HTTP triggered function executed successfully. Pass a name in the query string or in the request body for a personalized response.",
             status_code=200
        )

@app.route(route="upload")
def upload(req: func.HttpRequest) -> func.HttpResponse:
    content_type = req.headers.get('content-type')
    if not content_type:
        content_type = req.headers.get('Content-Type')
        if not content_type:
            return func.HttpResponse(
                "Content-Type header is missing. There is no way to determine the type of the content you are sending",
                status_code=400
            )

    if 'multipart/form-data' in content_type:
        try:
            # handle multipart form data
            form_data = parse_multipart_form_data(req)
            files = form_data.get('files')
            # print(files)
            responses = []
            for file_name, file_data in files.items():
                # parsed_data["files"][file.file_name] = {"length": len(f), "content": f}
                length = file_data.get('length')
                content = file_data.get('content')
                print(f"File {file_name} received with content length {length}")

                # save the file
                path = os.path.join(TMP_DIR, file_name)
                f = open(path, "wb")
                f.write(content)
                f.close()

                if '.pdf' in file_name:
                    # process the pdf file
                    response = pdf_handler.process_file(path)
                    print(response)
                    responses.append(response)
                elif '.png' in file_name or '.jpeg' in file_name or '.jpg' in file_name or '.webp' in file_name or '.gif' in file_name:
                    # process the image file
                    response = image_handler.process_file(path)
                    print(response)
                    responses.append(response)
                else:
                    responses.append({})

                # delete the file
                os.remove(path)
            return func.HttpResponse(
                json.dumps(responses),
                status_code=200
            )
        except Exception as e:
            traceback.print_exc()
            logging.error(f"Error processing multipart form data: {e}")
            return func.HttpResponse(
                "Error processing multipart form data",
                status_code=500
            )
    elif 'application/json' in content_type:
        # handle json
        print(req.get_json())
    elif 'application/pdf' in content_type:
        # handle pdf
        # get filename if available
        filename = req.headers.get('filename')
        time = datetime.datetime.now().strftime("%Y%m%d%H%M%S%f")

        if not filename:
            filename = f"{time}.pdf"

        path = os.path.join(TMP_DIR, filename)
        f = open(path, "wb")
        f.write(req.get_body())
        f.close()

        response = pdf_handler.process_file(path)
        print(response)
        os.remove(path)

        return func.HttpResponse(
            json.dumps(response),
            status_code=200
        )
    else:
        return func.HttpResponse(
            "This endpoint only accepts application/json and application/pdf",
            status_code=400
        )
    return func.HttpResponse(status_code=500)
