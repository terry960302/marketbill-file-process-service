import json
import os
from model import gateway_response


def health_check():
    env = dict(**os.environ)
    profile = str(env["PROFILE"])

    res = gateway_response.GatewayResponse(
        statusCode=200,
        body={"health": "[%s] Marketbill file process service is running...".format(profile)}
    )

    return json.dumps(res)
