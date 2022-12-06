import json
import os
import logging
from jsonpickle import encode
import boto3
from handler.root_handler import health_check
from handler.process_handler import process_file

logger = logging.getLogger()
logger.setLevel(logging.INFO)

client = boto3.client('lambda')
client.get_account_settings()


def lambda_handler(event, context):
    logger.info('## EVENT\r' + json.dumps(event))
    logger.info('## CONTEXT\r' + json.dumps(context))
    logger.info('## ENVIRONMENT VARIABLES\r' + json.dumps(dict(**os.environ)))

    if event['httpMethod'] == 'GET':
        return health_check()
    elif event['httpMethod'] == 'POST':
        data = dict(event["data"])
        return process_file(data)
    else:
        return {
            "statusCode": 403,
            "message": "Unsupported http method",
            "body": None,
        }
