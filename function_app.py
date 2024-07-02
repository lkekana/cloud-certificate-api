import datetime
import azure.functions as func
import logging
from file import hello_world
from utils import parse_multipart_form_data
import traceback
import llm.openai


app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)

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
            for file_name, file_data in files.items():
                # parsed_data["files"][file.file_name] = {"length": len(f), "content": f}
                length = file_data.get('length')
                content = file_data.get('content')
                print(f"File {file_name} received with content length {length}")
                # process the files
                pass
            # process the files
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
        print(f"Received a PDF file with filename {filename or time}.")
    else:
        return func.HttpResponse(
            "This endpoint only accepts application/json and application/pdf",
            status_code=400
        )
    return func.HttpResponse(status_code=200)
