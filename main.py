from fastapi import FastAPI, Request
from handler.root_handler import health_check
from handler.process_handler import handle_receipt_process
import os
import jpype

app = FastAPI()


@app.on_event("startup")
def on_start():
    def init_jvm():
        if jpype.isJVMStarted():
            return
        stream = os.popen('java -version')
        output = stream.read()
        print('JVM path : ', jpype.getDefaultJVMPath())
        jpype.startJVM(jpype.getDefaultJVMPath())
        jpype.java.lang.System.out.println("JVM checked from java functions")
        print(output)
    init_jvm()


@app.on_event("shutdown")
def on_shutdown():
    jpype.shutdownJVM()


@app.get("/")
def handle_root():
    return health_check()


@app.post("/")
async def handle_receipt(request: Request):
    json_object = await request.json()
    return handle_receipt_process(json_object)

# import json
# import os
# import logging
# from handler.root_handler import health_check
# from handler.process_handler import handle_receipt_process
# from model import gateway_response as r
#
# logger = logging.getLogger()
# logger.setLevel(logging.INFO)
#
#
# def lambda_handler(event, context):
#     method = "httpMethod"
#
#     logger.info('## EVENT\r' + json.dumps(event))
#     logger.info('## ENVIRONMENT VARIABLES\r' + json.dumps(dict(**os.environ)))
#
#     if event[method] == 'GET':
#         return health_check()
#     elif event[method] == 'POST':
#         body = event["body"]
#         return handle_receipt_process(body)
#     else:
#         return r.GatewayResponse(
#             statusCode=403,
#             body=r.ErrorBody(message="Unsupported http method").to_str()
#         )


# """ API gateway event JSON
# {
#     "resource": "/",
#     "path": "/",
#     "httpMethod": "GET",
#     "requestContext": {
#         "resourcePath": "/",
#         "httpMethod": "GET",
#         "path": "/Prod/",
#         ...
#     },
#     "headers": {
#         "accept": "text/html",
#         "accept-encoding": "gzip, deflate, br",
#         "Host": "xxx.us-east-2.amazonaws.com",
#         "User-Agent": "Mozilla/5.0",
#         ...
#     },
#     "multiValueHeaders": {
#         "accept": [
#             "text/html"
#         ],
#         "accept-encoding": [
#             "gzip, deflate, br"
#         ],
#         ...
#     },
#     "queryStringParameters": {
#         "postcode": 12345
#         },
#     "multiValueQueryStringParameters": null,
#     "pathParameters": null,
#     "stageVariables": null,
#     "body": null,
#     "isBase64Encoded": false
# }
# """
