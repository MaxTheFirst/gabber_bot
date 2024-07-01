from .models import *
from itertools import groupby


class DBManager():
    def __init__(self):
        db.create_tables([Chat, Settings])
        settings = Settings.select()
        if settings.count() == 0:
            self.settings = Settings.create()
        else:
            self.settings = settings[0]

    @property
    def config_channel_id(self):
        return self.settings.chat_id

    @config_channel_id.setter
    def config_channel_id(self, channel_id):
        self.settings.chat_id = channel_id
        self.settings.save()

    @property
    def moderator_mode(self) -> bool:
        return self.settings.moderator_mode

    @moderator_mode.setter
    def moderator_mode(self, is_mode: bool):
        self.settings.moderator_mode = is_mode
        self.settings.save()
    
    @property
    def is_delete(self) -> bool:
        return self.settings.is_delete

    @is_delete.setter
    def is_delete(self, is_mode: bool):
        self.settings.is_delete = is_mode
        self.settings.save()

    def get_group(self, iterable):
        return [i for i, _ in groupby(iterable)]

    def add_chats(self, out_ids, in_ids):
        data = [
            {'out_id': out_id, 'in_id': in_id}
            for out_id in out_ids
            for in_id in in_ids
            if out_id != in_id
        ]
        new_data = []
        data = self.get_group(data)
        for chat in data:
            flag = Chat.get_or_none(Chat.out_id == chat['in_id'], Chat.in_id == chat['in_id'])
            if not flag:
                new_data.append(chat)
        Chat.insert_many(new_data).execute()

    def get_chat_in_ids(self, out_id):
        chat_ids = [chat.in_id for chat in Chat.select(
            Chat.in_id).where(Chat.out_id == out_id)]
        if chat_ids:
            return self.get_group(chat_ids)
        return None

    @property
    def chats(self):
        return {
            chat.id: [chat.out_id, chat.in_id]
            for chat in Chat.select()
        }

    @property
    def chats_count(self):
        return Chat.select().count()

    def delete_chat(self, id):
        Chat.get(Chat.id == id).delete_instance()
      
if __name__ == '__main__':
    users = DBManager()
    users.add_chats([1, 1], [2, 2])
