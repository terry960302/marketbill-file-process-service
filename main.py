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


def parse_input():
    json_object = {
        "orderNo": "c3a5444d-b02d-42bf-ba2c-5d1d027dbe63",
        "retailer": {
            "name": "CCJBDFFVVW"
        },
        "wholesaler": {
            "name": "KQXYQVLXJA"
        },
        "orderItems": [
            {
                "flower": {
                    "name": "테데오옐로우",
                    "flowerType": {
                        "name": "국화"
                    }
                },
                "quantity": 17,
                "grade": "상",
                "price": 10000
            },
            {
                "flower": {
                    "name": "신명",
                    "flowerType": {
                        "name": "국화"
                    }
                },
                "quantity": 23,
                "grade": "상",
                "price": None
            },
            {
                "flower": {
                    "name": "상그릴라",
                    "flowerType": {
                        "name": "국화"
                    }
                },
                "quantity": 84,
                "grade": "상",
                "price": None
            }
        ]
    }

    print("@@@@ init")
    json_input = dto.ReceiptProcessInput(**json_object)
    pprint(json_input)


if __name__ == "__main__":
    print("out of function")
    parse_input()
