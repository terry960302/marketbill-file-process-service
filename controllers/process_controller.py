import json
import os

from fastapi import status
from services.receipt_service import ReceiptService
from models import receipt_process_input as dto, gateway_response as r
from datastore.datastore import Datastore
import traceback
import sys


def handle_receipt_process(req_body) -> r.GatewayResponse:
    try:
        # TODO: 다시 주석풀고 속도 영향 안가게 잘 배치할 필요가 있음
        # db = Datastore()
        # db.set_postgres()
        is_lambda_env = os.environ.get("LAMBDA_TASK_ROOT") is not None
        json_dict = json.loads(req_body) if is_lambda_env else dict(req_body)  # 람다 환경인지 로컬 환경인지에 따른 분기

        json_input = dto.ReceiptProcessInput(**json_dict)
        service = ReceiptService(json_input)
        output = service.process_receipt_pdf()

        return r.GatewayResponse(
            statusCode=status.HTTP_201_CREATED,
            body=r.ReceiptOutput(
                file_name=output.file_name,
                file_path=output.file_path,
                file_format=output.file_format,
                metadata=output.metadata
            ).to_str()).to_dict()

    except Exception as e:
        exc_info = sys.exc_info()
        ex = ''.join(traceback.format_exception(*exc_info))
        return r.GatewayResponse(
            statusCode=status.HTTP_500_INTERNAL_SERVER_ERROR,
            body=r.ErrorBody(message=ex).to_str()
        ).to_dict()
