import json
import os
import logging
from handler.root_handler import health_check
from handler.process_handler import process_file
from model import gateway_response as r

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(event, context):
    method = "httpMethod"

    logger.info('## EVENT\r' + json.dumps(event))
    logger.info('## ENVIRONMENT VARIABLES\r' + json.dumps(dict(**os.environ)))

    if event[method] == 'GET':
        return health_check()
    elif event[method] == 'POST':
        body = event["body"]
        return process_file(body)
    else:
        return r.GatewayResponse(
            statusCode=403,
            message="Unsupported http method"
        )


""" API gateway event JSON
{
    "resource": "/",
    "path": "/",
    "httpMethod": "GET",
    "requestContext": {
        "resourcePath": "/",
        "httpMethod": "GET",
        "path": "/Prod/",
        ...
    },
    "headers": {
        "accept": "text/html",
        "accept-encoding": "gzip, deflate, br",
        "Host": "xxx.us-east-2.amazonaws.com",
        "User-Agent": "Mozilla/5.0",
        ...
    },
    "multiValueHeaders": {
        "accept": [
            "text/html"
        ],
        "accept-encoding": [
            "gzip, deflate, br"
        ],
        ...
    },
    "queryStringParameters": {
        "postcode": 12345
        },
    "multiValueQueryStringParameters": null,
    "pathParameters": null,
    "stageVariables": null,
    "body": null,
    "isBase64Encoded": false
}
"""
