from peewee import *
import os
from models.receipt_process_logs import ReceiptProcessLogs
from models.base_model import db


class Datastore:

    def __init__(self):
        self.instance = None
        return

    def set_postgres(self):
        database = os.environ["DB_NAME"]
        user = os.environ["DB_USER"]
        password = os.environ["DB_PW"]
        host = os.environ["DB_HOST"]
        port = os.environ["DB_PORT"]
        pg_db = PostgresqlDatabase(database, user=user, password=password,
                                   host=host, port=port)
        self.instance = pg_db
        db.initialize(pg_db)

        self._auto_migrate()
        return

    def _auto_migrate(self):
        ReceiptProcessLogs.create_table()
        return
