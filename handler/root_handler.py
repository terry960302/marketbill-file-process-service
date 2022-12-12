import dataclasses
import json
from fastapi import status
import os
from model import gateway_response as r


def health_check():
    env = dict(**os.environ)
    profile = str(env["PROFILE"])

    return r.GatewayResponse(
        statusCode=status.HTTP_200_OK,
        body={"health": "[%s] Marketbill file process service is running...".format(profile)}
    ).to_dict()
