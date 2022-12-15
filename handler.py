import json
import os
import logging
from controllers.root_controller import health_check
from controllers.process_controller import handle_receipt_process
from models import gateway_response as r

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
        return handle_receipt_process(body)
    else:
        return r.GatewayResponse(
            statusCode=403,
            body=r.ErrorBody(message="Unsupported http method").to_str()
        )
