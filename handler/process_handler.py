import json

from service.receipt_service import ReceiptService
from model import receipt_process_input as dto, gateway_response as r


def process_file(json_dict):
    file_name = "sample_name"
    try:
        service = ReceiptService()
        json_input = dto.ReceiptProcessInput(**json_dict)
        service.process_receipt_data(json_input, file_name)

        return r.GatewayResponse(
            statusCode=200,
            body={
                "file_name": file_name,
                "file_path": "",
                "file_format": "pdf",
                "metadata": ""
            })

    except Exception as e:
        return r.GatewayResponse(
            statusCode=500,
            message=json.dumps(e),
        )
