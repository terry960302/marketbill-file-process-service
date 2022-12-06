import os
import logging
from jsonpickle import encode
import boto3

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# client = boto3.client('lambda')
# client.get_account_settings()

# def lambda_handler(event, context):
#     if event['httpMethod'] == 'GET':
#         return {
#             'statusCode': 200,
#             'body': jsonpickle.encode(event['queryStringParameters'])
#         }
#     if event['httpMethod'] == 'POST':
#         req_data = jsonpickle.encode(event['body']) # JSON 문자열 처리
#         return {
#             'statusCode': 200,
#             'body': jsonpickle.encode(req_data)
#         }
#     logger.info('## ENVIRONMENT VARIABLES\r' + jsonpickle.encode(dict(**os.environ)))
#     # logger.info('## EVENT\r' + jsonpickle.encode(event))
#     # logger.info('## CONTEXT\r' + jsonpickle.encode(context))
#     # response = client.get_account_settings()
#     # return response['AccountUsage']


def main():
    env = encode(dict(**os.environ))
    print(env)

if __name__ == "__main__":
    print("@@@@@@@@ hello world@@@@@@@")
    main()
