import json

from service.receipt_service import ReceiptService
from model import receipt_process_input as dto, gateway_response as r


def process_file(req_body):
    file_name = "sample_name"
    try:
        json_dict = {}
        if req_body is None:
            return r.GatewayResponse(
                statusCode=403,
                message="Unsupported format of request body for processing receipt."
            ).to_dict()
        else:
            json_dict = dict(req_body)

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
            }).to_dict()

    except Exception as e:
        return r.GatewayResponse(
            statusCode=500,
            message=json.dumps(e),
        ).to_dict()
