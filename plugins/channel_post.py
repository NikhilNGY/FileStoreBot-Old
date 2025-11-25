import random
import string
import asyncio
from pyrogram import filters, Client
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.enums import ParseMode
from pyrogram.errors import FloodWait
# Import the database instance
from helper.database import MongoDB

# --- Helper Method ---
def generate_random_id(length=8):
    """Generates a random alphanumeric string to act as the file_id."""
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

# Custom filter to prevent capturing numeric replies
async def is_not_numeric_reply(_, __, message: Message):
    if message.text and message.text.isdigit():
        return False
    return True

not_numeric_filter = filters.create(is_not_numeric_reply)


@Client.on_message(
    filters.private &
    ~filters.command(['start','users','broadcast','batch','genlink','usage', 'pbroadcast', 'ban', 'unban']) &
    not_numeric_filter
)
async def channel_post(client: Client, message: Message):
    if message.from_user.id not in client.admins:
        return await message.reply(client.reply_text)
    
    reply_text = await message.reply_text("Please Wait, processing file...", quote=True)
    
    try:
        # Copy the message to the DB Channel
        post_message = await message.copy(chat_id=client.db, disable_notification=True)
    except FloodWait as e:
        await asyncio.sleep(e.x)
        post_message = await message.copy(chat_id=client.db, disable_notification=True)
    except Exception as e:
        print(e)
        await reply_text.edit_text("Something went wrong. Could not save the file.")
        return
        
    # --- NEW LOGIC START ---
    # 1. Generate unique ID
    file_id = generate_random_id()
    
    # 2. Save to Database (Mapping: file_id -> message_id)
    await db.add_file(file_id, post_message.id)
    
    # 3. Generate Blogspot Link
    link = f"https://krpicture0.blogspot.com?start={file_id}"
    # --- NEW LOGIC END ---

    reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton("🔁 Share URL", url=f'https://telegram.me/share/url?url={link}')]])

    await reply_text.edit(
        f"<b>ʜᴇʀᴇ ɪꜱ ʏᴏᴜʀ ʟɪɴᴋ :</b>\n\n{link}", 
        reply_markup=reply_markup, 
        disable_web_page_preview=True,
        parse_mode=ParseMode.HTML
    )

    if not client.disable_btn:
        await post_message.edit_reply_markup(reply_markup)


@Client.on_message(filters.channel & filters.incoming)
async def new_post(client: Client, message: Message):
    # Check if message is from the configured DB channel
    if message.chat.id != client.db:
        return
    if client.disable_btn:
        return

    # --- NEW LOGIC START ---
    # 1. Generate unique ID
    file_id = generate_random_id()
    
    # 2. Save to Database
    await db.add_file(file_id, message.id)
    
    # 3. Generate Blogspot Link
    link = f"https://krpicture0.blogspot.com?start={file_id}"
    # --- NEW LOGIC END ---

    reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton("🔁 Share URL", url=f'https://telegram.me/share/url?url={link}')]])
    
    try:
        await message.edit_reply_markup(reply_markup)
    except Exception as e:
        print(e)
        pass

