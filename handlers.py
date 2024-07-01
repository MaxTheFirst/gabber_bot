import textes
import my_filtres
import re
import asyncio 
from dispatcher import app, user_db
from pyrogram import Client, filters
from pyrogram.types import Message, Chat
from pyrogram.errors import BadRequest

async def send_message(text):
    await app.send_message(
        chat_id=user_db.config_channel_id,
        text=text
    )

def error_dec(func):
    async def wrapper(_, message: Message):
        try:
            all_good = await func(_, message)
            if not all_good:
                raise BadRequest
        except BadRequest or ValueError:
            await send_message(textes.READ_ERROR)
            return
    return wrapper


def get_msg_args(text: str):
    if text:
        args = re.findall(r'(?:(?<=id)|@)\S+[^,\s]', text)
    else:
        args = []
    return args, len(args)

@app.on_message(filters.me & filters.channel & ~my_filtres.moderator_chat & filters.command(textes.START_COMMAND, prefixes=textes.PREFIX))
async def set_config_chat(_, message: Message):
    user_db.config_channel_id = message.chat.id
    await send_message(textes.HELLOW)

async def get_chats(chats):
    results = []
    for chat in chats:
        results.append(await app.get_chat(chat))
        await asyncio.sleep(0.5)
    return {chat.id: chat for chat in results}
   
@app.on_message(my_filtres.moderator_chat & filters.command(textes.ADD_CHAT_COMMAND, prefixes=textes.PREFIX))
@error_dec
async def add_chats(_, message: Message):
    chats = message.text.split('>', maxsplit=1)
    data = []
    for chat_names in chats:
        if not chat_names:
            continue
        chat_names, _ = get_msg_args(chat_names)
        chats = await get_chats(chat_names)
        data.append(chats)
    if len(data) == 2:
        user_db.add_chats(*[chat_data.keys() for chat_data in data])
        await send_message(textes.ADD_SAVED)
        return True
    

@app.on_message(my_filtres.moderator_chat & filters.command(textes.MODERATOR_COMMAND, prefixes=textes.PREFIX))
async def add_chats(_, message: Message):
    moderator_mode = not user_db.moderator_mode
    user_db.moderator_mode = moderator_mode
    text = textes.MODERATOR_TEXT.format(textes.MODERATOR[bool(moderator_mode)])
    await send_message(text)

def get_chat_name(chat: Chat):
    if chat.username:
        return f'@{chat.username}'
    return chat.title or chat.first_name

@app.on_message(my_filtres.moderator_chat & filters.command(textes.DEL_CHAT_COMMAND, prefixes=textes.PREFIX))
async def delete_chats(_, message: Message):
    if user_db.chats_count == 0:
        await send_message(textes.NO_COUPLES)
        return
    chats = user_db.chats
    chats_ids = []
    for i in chats.values():
        for j in i:
            chats_ids.append(j)
    chats_data = await get_chats(chats_ids)
    text = ''
    count = 1
    for chat in chats:
        text += f'{count}. ' + '{} > {}'.format(*[get_chat_name(chats_data[i]) for i in chats[chat]]) + '\n'
        count += 1
    msg = textes.DELETE_TEXT.format(text)
    await send_message(msg)
    user_db.is_delete = True    

def get_forward(message: Message):
    return message.forward_from or message.forward_from_chat

@app.on_message(my_filtres.moderator_chat & filters.command(textes.POST, prefixes=textes.PREFIX) & filters.forwarded)
@error_dec
async def posted(client: Client, message: Message):
    args, len_args = get_msg_args(message.text)
    if len_args == 1:
        forward_msg = get_forward(message.text)
        await client.copy_message(args[0], forward_msg.id, message.forward_from_message_id)
        return True

@app.on_message(my_filtres.moderator_chat & filters.command(textes.POST, prefixes=textes.PREFIX))
@error_dec
async def posted_in_this(client: Client, message: Message):
    args, len_args = get_msg_args(message.text)
    if len_args == 2:
        await client.copy_message(args[1], message.chat.id, int(args[0]))
        return True

def get_forward_chat_id(message: Message):
    return get_forward(message).id

@app.on_message(my_filtres.moderator_chat & filters.forwarded)
async def get_id(_, message: Message):
    await send_message(f'id{get_forward_chat_id(message)}')

@app.on_message(my_filtres.moderator_chat & filters.regex(r'\d+') & my_filtres.delete)
@error_dec
async def get_id(_, message: Message):
    index = int(message.text)
    if index >= 0 and index <= user_db.chats_count:
        user_db.delete_chat(index)
        await send_message(textes.DELETE_SAVED)
        user_db.is_delete = False
        return True

@app.on_message(~my_filtres.moderator_chat)
async def copy(client: Client, message: Message):
    ids = user_db.get_chat_in_ids(message.chat.id)
    if ids:
        if user_db.moderator_mode:
            if user_db.config_channel_id != 0:
                chats = await get_chats(ids)
                msg = await client.copy_message(user_db.config_channel_id, message.chat.id, message.message_id)
                for id in ids:
                    text = textes.POST_TEXT.format(get_chat_name(message.chat), get_chat_name(chats[id]))
                    command = textes.PREFIX + textes.POST + f' id{msg.message_id} > id{id}'
                    await send_message(text)
                    await send_message(command)
        else:
            for id in ids:
                await client.copy_message(id, message.chat.id, message.message_id)