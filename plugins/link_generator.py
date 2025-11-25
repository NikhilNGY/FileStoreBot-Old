import random
import string
import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.enums import ParseMode
from pyrogram.errors.pyromod import ListenerTimeout
from helper.helper_func import get_message_id
# Import the database instance we created in database.py
from helper.database import MongoDB

# --- Helper Methods ---

def generate_random_id(length=8):
    """Generates a random alphanumeric string to act as the file_id."""
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

async def ask_for_message(client, user_id, prompt_text):
    """A helper function to ask for a message and listen for the response."""
    prompt_message = await client.send_message(user_id, prompt_text, parse_mode=ParseMode.HTML)
    try:
        response = await client.listen(chat_id=user_id, filters=(filters.forwarded | (filters.text & ~filters.forwarded)), timeout=60)
        await prompt_message.delete()
        return response
    except ListenerTimeout:
        await prompt_message.edit("<b>Timeout!</b> Please try the command again.")
        return None

# --- Bot Commands ---

@Client.on_message(filters.private & filters.command('batch'))
async def batch(client: Client, message: Message):
    # Check if user is admin (assuming client.admins is set in your main file)
    if hasattr(client, 'admins') and message.from_user.id not in client.admins:
        # Fallback text if client.reply_text isn't set
        text = getattr(client, 'reply_text', "You are not authorized.")
        return await message.reply(text)
    
    # 1. Get First Message
    while True:
        first_message = await ask_for_message(client, message.from_user.id, "Forward the <b>First Message</b> from the DB Channel (with quotes), or send its link.")
        if not first_message: return

        f_msg_id = await get_message_id(client, first_message)
        if f_msg_id:
            break
        else:
            await first_message.reply("❌ <b>Invalid Message</b>\n\nThis message is not from the configured DB Channel. Please try again.", quote=True)

    # 2. Get Last Message
    while True:
        second_message = await ask_for_message(client, message.from_user.id, "Now, forward the <b>Last Message</b> from the DB Channel (with quotes), or send its link.")
        if not second_message: return

        s_msg_id = await get_message_id(client, second_message)
        if s_msg_id:
            break
        else:
            await second_message.reply("❌ <b>Invalid Message</b>\n\nThis message is not from the configured DB Channel. Please try again.", quote=True)

    # 3. Generate ID and Save to DB
    file_id = generate_random_id()
    
    # Save to MongoDB (Start ID and End ID)
    await db.add_file(file_id, f_msg_id, s_msg_id)
    
    # 4. Generate Link
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
    # Check if user is admin
    if hasattr(client, 'admins') and message.from_user.id not in client.admins:
        text = getattr(client, 'reply_text', "You are not authorized.")
        return await message.reply(text)
    
    # 1. Get Message
    while True:
        channel_message = await ask_for_message(client, message.from_user.id, "Forward a message from the DB Channel (with quotes), or send its link.")
        if not channel_message: return

        msg_id = await get_message_id(client, channel_message)
        if msg_id:
            break
        else:
            await channel_message.reply("❌ <b>Invalid Message</b>\n\nThis message is not from the configured DB Channel. Please try again.", quote=True)

    # 2. Generate ID and Save to DB
    file_id = generate_random_id()
    
    # Save to MongoDB (Only Start ID, To ID is None)
    await db.add_file(file_id, msg_id, to_id=None)
    
    # 3. Generate Link
    link = f"https://krpicture0.blogspot.com?start={file_id}"

    reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton("🔁 Share URL", url=f'https://telegram.me/share/url?url={link}')]])

    await channel_message.reply_text(
        f"<b>Generated Link:</b>\n\n{link}", 
        quote=True, 
        reply_markup=reply_markup,
        parse_mode=ParseMode.HTML
    )

