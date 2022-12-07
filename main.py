import json
import os
import logging
import boto3
from handler.root_handler import health_check
from handler.process_handler import process_file
from model import receipt_process_input as dto, gateway_response as r
from pprint import pprint

logger = logging.getLogger()
logger.setLevel(logging.INFO)

client = boto3.client('lambda')
client.get_account_settings()


def lambda_handler(event, context):
    method = "httpMethod"

    logger.info('## EVENT\r' + json.dumps(event))
    logger.info('## CONTEXT\r' + json.dumps(context))
    logger.info('## ENVIRONMENT VARIABLES\r' + json.dumps(dict(**os.environ)))

    if event[method] == 'GET':
        return health_check()
    elif event[method] == 'POST':
        json_dict = dict(event["data"])
        return process_file(json_dict)
    else:
        return r.GatewayResponse(
            statusCode=403,
            message="Unsupported http method"
        )