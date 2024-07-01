from peewee import *

db = SqliteDatabase('db/users_data.db')


class BaseModel(Model):
    class Meta:
        database = db

class Settings(BaseModel):
    chat_id = IntegerField(default=0)
    moderator_mode = BooleanField(default=False)
    is_delete = BooleanField(default=False)

    class Meta:
        db_table = 'settings'

class Chat(BaseModel):
    id = PrimaryKeyField()
    out_id = IntegerField(default=0)
    in_id = IntegerField(default=0)

    class Meta:
        db_table = 'chats'

