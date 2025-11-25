import asyncio
from datetime import timedelta
import humanize
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.enums import ParseMode
from pyrogram.errors import FloodWait
from helper.helper_func import get_messages, force_sub, delete_files

@Client.on_message(filters.command('start') & filters.private)
@force_sub
async def start_command(client: Client, message: Message):
    user_id = message.from_user.id
    
    # --- User Management ---
    present = await client.mongodb.present_user(user_id)
    if not present:
        try:
            await client.mongodb.add_user(user_id)
        except Exception as e:
            client.LOGGER(__name__, client.name).warning(f"Error adding a user:\n{e}")
            
    is_banned = await client.mongodb.is_banned(user_id)
    if is_banned:
        return await message.reply("**You have been banned from using this bot!**")
    
    text = message.text
    if len(text) > 7:
        # --- NEW LOGIC: Retrieve from Database ---
        try:
            file_id = text.split(" ", 1)[1]
        except IndexError:
            return

        # Fetch file details from MongoDB using the file_id
        file_data = await client.mongodb.get_file(file_id)
        
        if not file_data:
            return await message.reply("<b>Link Invalid or Expired.</b>")

        # Extract Start and End IDs
        try:
            from_id = int(file_data["from_id"])
            to_id = file_data.get("to_id")
            to_id = int(to_id) if to_id else None
        except (KeyError, ValueError):
             return await message.reply("<b>Error: File data corrupted.</b>")

        # Calculate range of messages
        ids = []
        if to_id:
            ids = list(range(from_id, to_id + 1))
        else:
            ids = [from_id]
        
        # --- Fetch Messages ---
        temp_msg = await message.reply("Please wait, fetching your files...")
        
        messages = []
        try:
            messages = await get_messages(client, ids)
        except Exception as e:
            await temp_msg.edit_text("Something went wrong while fetching files.")
            client.LOGGER(__name__, client.name).warning(f"Error getting messages: {e}")
            return
        
        if not messages:
            await temp_msg.edit("Couldn't find the files in the database.")
            return
        
        await temp_msg.delete()

        # --- Send Messages ---
        yugen_msgs = []

        for msg in messages:
            caption = msg.caption.html if msg.caption else ""
            reply_markup = msg.reply_markup if not client.disable_btn else None

            try:
                copied_msg = await msg.copy(
                    chat_id=message.from_user.id, 
                    caption=caption, 
                    reply_markup=reply_markup, 
                    protect_content=client.protect,
                    parse_mode=ParseMode.HTML
                )
                yugen_msgs.append(copied_msg)
            except FloodWait as e:
                await asyncio.sleep(e.x)
                copied_msg = await msg.copy(
                    chat_id=message.from_user.id, 
                    caption=caption, 
                    reply_markup=reply_markup, 
                    protect_content=client.protect,
                    parse_mode=ParseMode.HTML
                )
                yugen_msgs.append(copied_msg)
            except Exception as e:
                client.LOGGER(__name__, client.name).warning(f"Failed to send message: {e}")
                pass
        
        # --- Auto Deletion Logic ---
        if yugen_msgs and client.auto_del > 0:
            enter = text
            k = await client.send_message(
                chat_id=message.from_user.id, 
                text=f'<blockquote><b><i>These files will be deleted in {humanize.naturaldelta(timedelta(seconds=client.auto_del))}. Please save them.</i></b></blockquote>',
                parse_mode=ParseMode.HTML
            )
            asyncio.create_task(delete_files(yugen_msgs, client, k, enter))
    
    else:
        # --- Standard Start Message (No Link) ---
        buttons = [[InlineKeyboardButton("ʜᴇʟᴘ", callback_data = "about"), InlineKeyboardButton("ᴄʟᴏꜱᴇ", callback_data = "close")]]
        if user_id in client.admins:
            buttons.insert(0, [InlineKeyboardButton("⛩️ ꜱᴇᴛᴛɪɴɢꜱ ⛩️", callback_data="settings")])
        
        photo = client.messages.get("START_PHOTO", "")
        
        start_text = client.messages.get('START', 'No Start Message').format(
            first=message.from_user.first_name,
            last=message.from_user.last_name,
            username=None if not message.from_user.username else '@' + message.from_user.username,
            mention=message.from_user.mention,
            id=message.from_user.id
        )

        if photo:
            await client.send_photo(
                chat_id=message.chat.id,
                photo=photo,
                caption=start_text,
                reply_markup=InlineKeyboardMarkup(buttons),
                parse_mode=ParseMode.HTML
            )
        else:
            await client.send_message(
                chat_id=message.chat.id,
                text=start_text,
                reply_markup=InlineKeyboardMarkup(buttons),
                parse_mode=ParseMode.HTML
            )
