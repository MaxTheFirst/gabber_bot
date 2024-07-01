from dispatcher import user_db
from pyrogram import filters
from pyrogram.types import Message


async def is_moderator_chat(_, __, query: Message):
    return query.chat.id == user_db.config_channel_id

moderator_chat = filters.create(is_moderator_chat)

async def is_delete(_, __, query: Message):
    return user_db.is_delete
    
delete = filters.create(is_delete)
