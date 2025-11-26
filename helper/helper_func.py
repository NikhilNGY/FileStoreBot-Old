import re
import asyncio
import random
import string
from pyrogram import filters, Client
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.enums import ChatMemberStatus, ParseMode
from pyrogram.errors import UserNotParticipant, Forbidden, PeerIdInvalid, ChatAdminRequired, FloodWait, MessageIdInvalid
from datetime import datetime, timedelta
from pyrogram import errors

# --- New Method: Random ID Generator ---
def generate_random_id(length=8):
    """Generates a random alphanumeric string to act as the file_id."""
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

# --- Message Retrieval Methods ---

async def get_messages(client, message_ids):
    messages = []
    total_messages = 0
    while total_messages != len(message_ids):
        temb_ids = message_ids[total_messages:total_messages+200]
        try:
            msgs = await client.get_messages(
                chat_id=client.db,
                message_ids=temb_ids
            )
        except FloodWait as e:
            await asyncio.sleep(e.x)
            msgs = await client.get_messages(
                chat_id=client.db,
                message_ids=temb_ids
            )
        except Exception:
            msgs = []
            pass
        total_messages += len(temb_ids)
        messages.extend(msgs)
    return messages

async def get_message_id(client, message):
    if message.forward_from_chat:
        if message.forward_from_chat.id == client.db:
            return message.forward_from_message_id
        else:
            return 0
    elif message.forward_sender_name:
        return 0
    elif message.text:
        # Regex to handle https://t.me/ and https://telegram.me/
        pattern = r"https://(?:t|telegram)\.me/(?:c/)?(.*)/(\d+)"
        matches = re.match(pattern, message.text)
        if not matches:
            return 0
        channel_id = matches.group(1)
        msg_id = int(matches.group(2))
        
        # Check if the link belongs to the DB channel
        if channel_id.isdigit():
            if f"-100{channel_id}" == str(client.db):
                return msg_id
        else:
            # Handle username based links
            if hasattr(client, 'db_channel') and client.db_channel.username and channel_id == client.db_channel.username:
                return msg_id
    return 0

# --- Utility Methods ---

def get_readable_time(seconds: int) -> str:
    count = 0
    up_time = ""
    time_list = []
    time_suffix_list = ["s", "m", "h", "days"]
    while count < 4:
        count += 1
        remainder, result = divmod(seconds, 60) if count < 3 else divmod(seconds, 24)
        if seconds == 0 and remainder == 0:
            break
        time_list.append(int(result))
        seconds = int(remainder)
    hmm = len(time_list)
    for x in range(hmm):
        time_list[x] = str(time_list[x]) + time_suffix_list[x]
    if len(time_list) == 4:
        up_time += f"{time_list.pop()}, "
    time_list.reverse()
    up_time += ":".join(time_list)
    return up_time

async def is_bot_admin(client, channel_id):
    try:
        bot = await client.get_chat_member(channel_id, "me")
        if bot.status in (ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER):
            if bot.privileges:
                required_rights = ["can_invite_users", "can_delete_messages"]
                missing_rights = [right for right in required_rights if not getattr(bot.privileges, right, False)]
                if missing_rights:
                    return False, f"Bot is missing the following rights: {', '.join(missing_rights)}"
            return True, None
        return False, "Bot is not an admin in the channel."
    except errors.ChatAdminRequired:
        return False, "Bot lacks permission to access admin information in this channel."
    except Exception as e:
        return False, f"Unexpected error: {str(e)}"

# --- Force Sub Methods ---

async def check_subscription(client, user_id):
    statuses = {}
    if not hasattr(client, 'fsub_dict') or not client.fsub_dict:
        return statuses

    for channel_id, (channel_name, channel_link, request, timer) in client.fsub_dict.items():
        if request:
            # Using the new DB instance logic if available
            send_req = await client.mongodb.is_user_in_channel(channel_id, user_id) if hasattr(client, 'mongodb') else False
            if send_req:
                statuses[channel_id] = ChatMemberStatus.MEMBER
                continue
        try:
            user = await client.get_chat_member(channel_id, user_id)
            statuses[channel_id] = user.status
        except UserNotParticipant:
            statuses[channel_id] = ChatMemberStatus.BANNED
        except Forbidden:
            # Use getattr to avoid crash if LOGGER isn't set up yet
            logger = getattr(client, 'LOGGER', print)
            logger(__name__, client.name).warning(f"Bot lacks permission for {channel_name}.")
            statuses[channel_id] = None
        except Exception as e:
            logger = getattr(client, 'LOGGER', print)
            logger(__name__, client.name).warning(f"Error checking {channel_name}: {e}")
            statuses[channel_id] = None
    return statuses


def is_user_subscribed(statuses):
    return all(
        status in {ChatMemberStatus.MEMBER, ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER}
        for status in statuses.values() if status is not None
    ) and bool(statuses)


def force_sub(func):
    """Decorator to enforce force subscription with a beautiful status message."""
    async def wrapper(client: Client, message: Message):
        if not hasattr(client, 'fsub_dict') or not client.fsub_dict:
            return await func(client, message)
        
        # Safely get messages or default
        msgs_config = getattr(client, 'messages', {})
        photo = msgs_config.get('FSUB_PHOTO', '')
        
        if photo:
            msg = await message.reply_photo(caption="<code>Checking subscription...</code>", photo=photo, parse_mode=ParseMode.HTML)
        else:
            msg = await message.reply("<code>Checking subscription...</code>", parse_mode=ParseMode.HTML)
        
        user_id = message.from_user.id
        statuses = await check_subscription(client, user_id)

        if is_user_subscribed(statuses):
            await msg.delete()
            return await func(client, message)

        buttons = []
        
        # --- THIS IS THE BEAUTIFIED PART ---
        status_lines = []
        for c, (channel_id, (channel_name, channel_link, request, timer)) in enumerate(client.fsub_dict.items(), 1):
            status = statuses.get(channel_id)
            
            # Set status text with HTML formatting
            if status in {ChatMemberStatus.MEMBER, ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER}:
                status_text = "<b>Joined</b> ✅"
            else:
                status_text = "<i>Required</i> ❗️"
                # Add a join button only if not joined
                if timer > 0:
                    try:
                        expire_time = datetime.now() + timedelta(minutes=timer)
                        invite = await client.create_chat_invite_link(chat_id=channel_id, expire_date=expire_time, creates_join_request=request)
                        channel_link = invite.invite_link
                    except Exception:
                        pass # Fallback to original link if error
                buttons.append(InlineKeyboardButton(f"Join {channel_name}", url=channel_link))

            status_lines.append(f"› {channel_name} - {status_text}")
        
        fsub_text = msgs_config.get('FSUB', "<blockquote><b>Join Required</b></blockquote>\nYou must join the following channel(s) to continue:")
        channels_message = f"{fsub_text}\n\n" + "\n".join(status_lines)
        # --- END OF BEAUTIFIED PART ---

        from_link = message.text.split(" ")
        if len(from_link) > 1:
            try_again_link = f"https://krpicture0.blogspot.com/?start={from_link[1]}"
            try_again_button = [InlineKeyboardButton("🔄 Try Again", url=try_again_link)]
        else:
            try_again_button = []

        # Organize buttons
        button_layout = [buttons[i:i + 2] for i in range(0, len(buttons), 2)]
        if try_again_button:
            button_layout.append(try_again_button)
            
        buttons_markup = InlineKeyboardMarkup(button_layout) if button_layout else None
        
        try:
            await msg.edit_text(text=channels_message, reply_markup=buttons_markup, parse_mode=ParseMode.HTML)
        except Exception as e:
            logger = getattr(client, 'LOGGER', print)
            logger(__name__, client.name).warning(f"Error updating FSUB message: {e}")

    return wrapper

async def delete_files(messages, client, k, enter):
    if client.auto_del > 0:
        await asyncio.sleep(client.auto_del)
        for msg in messages:
            try:
                await msg.delete()
            except Exception as e:
                logger = getattr(client, 'LOGGER', print)
                logger(__name__, client.name).warning(f"Failed to auto-delete message {msg.id}: {e}")
    
    command_part = enter.split(" ")[1] if len(enter.split(" ")) > 1 else None
    keyboard = None
    if command_part:
        # Reconstruct the link using the new File ID format
        button_url = f"https://t.me/linkz_ki_duniyaa"
        keyboard = InlineKeyboardMarkup(
            [[InlineKeyboardButton("•  BACKUP CHANNEL  •", url=button_url)]]
        )
    
    # --- FIX: Added try/except block here ---
    try:
        await k.edit_text(
            "<blockquote><b><i>Your file has been deleted. If You Want Again File Then Again Open link In Channel</i></b></blockquote>",
            reply_markup=keyboard,
            parse_mode=ParseMode.HTML
        )
    except Exception:
        # Message likely deleted by user, safe to ignore
        pass
