from peewee import *
import datetime
from models.base_model import BaseModel


class ReceiptProcessLogs(BaseModel):
    id = BigAutoField(primary_key=True, unique=True)
    status = TextField()
    input_data = TextField()
    output_date = TextField()
    err_logs = TextField()
    created_at = DateTimeField(default=datetime.datetime.now)
    updated_at = DateTimeField(default=datetime.datetime.now)
    deleted_at = DateTimeField()
