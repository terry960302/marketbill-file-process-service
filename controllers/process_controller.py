import json
import os
from fastapi import status
from services.receipt_service import ReceiptService
from models import receipt_process_input as dto, gateway_response as r
import inspect
import logging
from constants import strings

# 로그
logger = logging.getLogger("process_controller")
logging.basicConfig(format=strings.LOGGER_FORMAT)
logger.setLevel(logging.INFO)


def handle_receipt_process(req_body) -> r.GatewayResponse:
    func_name = inspect.stack()[0][3]
    try:
        is_lambda_env = os.environ.get(
            "LAMBDA_TASK_ROOT") is not None  # 람다 환경인지 로컬 환경인지에 따른 분기(로컬에선 테스트용이성을 위해 fastApi 사용)
        json_dict = json.loads(req_body) if is_lambda_env else dict(req_body)

        # logger.info(f'${func_name} > request body : \r{json.dumps(json_dict)}')

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
        msg = f'Failed handle_receipt_process : {e}'
        logger.error(msg)
        return r.GatewayResponse(
            statusCode=status.HTTP_500_INTERNAL_SERVER_ERROR,
            body=r.ErrorBody(message=msg).to_str()
        ).to_dict()
