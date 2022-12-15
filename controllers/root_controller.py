import dataclasses
import json
from fastapi import status
import os
from models import gateway_response as r


def health_check():
    env = dict(**os.environ)
    profile = str(env["PROFILE"])

    return r.GatewayResponse(
        statusCode=status.HTTP_200_OK,
        body=json.dumps({"health": "[%s] Marketbill file process services is running...".format(profile)})
    ).to_dict()
