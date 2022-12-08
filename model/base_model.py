from peewee import DatabaseProxy, Model

db = DatabaseProxy()  # Create a proxy for our db.


class BaseModel(Model):
    class Meta:
        database = db
