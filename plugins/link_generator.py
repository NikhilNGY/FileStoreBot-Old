import random
import string
import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.enums import ParseMode
from pyrogram.errors.pyromod import ListenerTimeout
from helper.helper_func import get_message_id

# --- Helper Methods ---

def generate_random_id(length=8):
    """Generates a random alphanumeric string to act as the file_id."""
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

async def save_to_db(client, file_id, from_id, to_id=None):
    """
    Saves the mapping to MongoDB.
    Structure: { "file_id": file_id, "from": start_msg_id, "to": end_msg_id }
    """
    # PLACEHOLDER: Connect to your actual MongoDB here
    # await client.db_collection.insert_one({
    #     "file_id": file_id,
    #     "from_id": from_id,
    #     "to_id": to_id, 
    #     "created_at": datetime.now()
    # })
    print(f"Simulating Save to DB: File ID={file_id} | From={from_id} | To={to_id}")
    return True

# --- Bot Commands ---

async def ask_for_message(client, user_id, prompt_text):
    prompt_message = await client.send_message(user_id, prompt_text, parse_mode=ParseMode.HTML)
    try:
        response = await client.listen(chat_id=user_id, filters=(filters.forwarded | (filters.text & ~filters.forwarded)), timeout=60)
        await prompt_message.delete()
        return response
    except ListenerTimeout:
        await prompt_message.edit("<b>Timeout!</b> Please try the command again.")
        return None

@Client.on_message(filters.private & filters.command('batch'))
async def batch(client: Client, message: Message):
    if message.from_user.id not in client.admins:
        return await message.reply(client.reply_text)
    
    while True:
        first_message = await ask_for_message(client, message.from_user.id, "Forward the <b>First Message</b> from the DB Channel (with quotes), or send its link.")
        if not first_message: return

        f_msg_id = await get_message_id(client, first_message)
        if f_msg_id:
            break
        else:
            await first_message.reply("❌ <b>Invalid Message</b>\n\nThis message is not from the configured DB Channel. Please try again.", quote=True)

    while True:
        second_message = await ask_for_message(client, message.from_user.id, "Now, forward the <b>Last Message</b> from the DB Channel (with quotes), or send its link.")
        if not second_message: return

        s_msg_id = await get_message_id(client, second_message)
        if s_msg_id:
            break
        else:
            await second_message.reply("❌ <b>Invalid Message</b>\n\nThis message is not from the configured DB Channel. Please try again.", quote=True)

    # 1. Generate the unique ID (file_id)
    file_id = generate_random_id()
    
    # 2. Save to MongoDB using the file_id
    await save_to_db(client, file_id, f_msg_id, s_msg_id)
    
    # 3. Create Link with file_id
    link = f"https://krpicture0.blogspot.com?start={file_id}"
    
    reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton("🔁 Share URL", url=f'https://telegram.me/share/url?url={link}')]])
    
    await second_message.reply_text(
        f"<b>ʜᴇʀᴇ ɪꜱ ʏᴏᴜʀ ʟɪɴᴋ :</b>\n\n{link}", 
        quote=True, 
        reply_markup=reply_markup,
        parse_mode=ParseMode.HTML
    )


@Client.on_message(filters.private & filters.command('genlink'))
async def link_generator(client: Client, message: Message):
    if message.from_user.id not in client.admins:
        return await message.reply(client.reply_text)
    
    while True:
        channel_message = await ask_for_message(client, message.from_user.id, "Forward a message from the DB Channel (with quotes), or send its link.")
        if not channel_message: return

        msg_id = await get_message_id(client, channel_message)
        if msg_id:
            break
        else:
            await channel_message.reply("❌ <b>Invalid Message</b>\n\nThis message is not from the configured DB Channel. Please try again.", quote=True)

    # 1. Generate the unique ID (file_id)
    file_id = generate_random_id()
    
    # 2. Save to MongoDB using the file_id
    await save_to_db(client, file_id, msg_id, to_id=None)
    
    # 3. Create Link with file_id
    link = f"https://krpicture0.blogspot.com?start={file_id}"

    reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton("🔁 Share URL", url=f'https://telegram.me/share/url?url={link}')]])

    await channel_message.reply_text(
        f"<b>Generated Link:</b>\n\n{link}", 
        quote=True, 
        reply_markup=reply_markup,
        parse_mode=ParseMode.HTML
    )
