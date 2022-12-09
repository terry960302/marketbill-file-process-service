import json

from service.receipt_service import ReceiptService
from model import receipt_process_input as dto, gateway_response as r
from datastore.datastore import Datastore


def handle_receipt_process(req_body):
    try:
        db = Datastore()
        db.set_postgres()

        json_dict = dict(req_body)

        receipt_form_name = 'receipt_001'
        json_input = dto.ReceiptProcessInput(**json_dict)
        service = ReceiptService(json_input, receipt_form_name)
        output = service.process_receipt_from_local()

        return r.GatewayResponse(
            statusCode=200,
            body=r.ReceiptOutput(
                file_name=output.file_name,
                file_path=output.file_path,
                file_format=output.file_format,
                metadata=output.metadata
            ).to_str()).to_dict()

    except Exception as e:
        return r.GatewayResponse(
            statusCode=500,
            body=r.ErrorBody(message=json.dumps(e)).to_str()
        ).to_dict()
