import dataclasses
import json
import os
from model import gateway_response as r


def health_check():
    env = dict(**os.environ)
    profile = str(env["PROFILE"])

    res = r.GatewayResponse(
        statusCode=200,
        body={"health": "[%s] Marketbill file process service is running...".format(profile)}
    )
    return res.to_dict()
