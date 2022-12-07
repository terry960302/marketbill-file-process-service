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
