import json

from service.generate_receipt import process_receipt_data


def process_file(data):
    file_name = "sample_name"
    try:
        process_receipt_data(data, file_name)
        return {
            'statusCode': 200,
            'body': json.dumps({
                "file_name": file_name,
                "file_path": "",
                "file_format": "pdf",
                "metadata": ""
            })
        }
    except Exception as e:
        return {
            'statusCode': 500,
            "message": json.dumps(e),
            'body': None,
        }
