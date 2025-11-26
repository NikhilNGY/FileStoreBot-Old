# Made by @NaapaExtra for @Realm_Bots 

from aiohttp import web
from plugins import web_server
import sys
import asyncio
from datetime import datetime
from pyrogram import Client, filters
from pyrogram.enums import ParseMode
from pyrogram.errors import FloodWait
from pyrogram.handlers import MessageHandler 
from pyrogram.types import Message

# Config imports
from config import LOGGER, PORT, OWNER_ID

# Import the Database class
from helper.database import MongoDB  

version = "v1.0.0"

class Bot(Client):
    def __init__(self, session, workers, db, fsub, token, admins, messages, auto_del, db_uri, db_name, api_id, api_hash, protect, disable_btn):
        super().__init__(
            name=session,
            api_hash=api_hash,
            api_id=api_id,
            plugins={
                "root": "plugins"
            },
            workers=workers,
            bot_token=token
        )
        self.LOGGER = LOGGER
        self.name = session
        
        # --- Handle Multiple Database Channels (Supports String or List from JSON) ---
        self.db_channels = []
        try:
            if isinstance(db, list):
                self.db_channels = [int(x) for x in db]
            elif isinstance(db, str):
                # Handle comma separated string if passed
                if "," in db:
                    self.db_channels = [int(x.strip()) for x in db.split(",") if x.strip().lstrip("-").isdigit()]
                else:
                    self.db_channels = [int(db)]
            else:
                self.db_channels = [int(db)]
        except Exception as e:
            self.LOGGER(__name__, self.name).warning(f"DB Channel ID format warning: {e}")
            # Fallback
            if isinstance(db, list):
                self.db_channels = db
            else:
                self.db_channels = [db]

        # Set the PRIMARY DB (The first one) for saving new files
        self.db = self.db_channels[0]
        # ----------------------------------------------------

        self.fsub = fsub
        self.owner = OWNER_ID
        self.fsub_dict = {}
        self.admins = admins + [OWNER_ID] if OWNER_ID not in admins else admins
        self.messages = messages
        self.auto_del = auto_del
        self.protect = protect
        self.req_fsub = {}
        self.disable_btn = disable_btn
        self.reply_text = messages.get('REPLY', 'Do not send any useless message in the bot.')
        
        # Initialize the Database Class
        self.mongodb = MongoDB(db_uri, db_name)
        self.req_channels = []
    
    def get_current_settings(self):
        """Returns a dictionary of the current settings to be saved."""
        return {
            "admins": self.admins,
            "messages": self.messages,
            "auto_del": self.auto_del,
            "protect": self.protect,
            "disable_btn": self.disable_btn,
            "reply_text": self.reply_text,
            "fsub": self.fsub
        }

    # --- AUTO DELETE PM MEDIA HANDLER ---
    async def auto_delete_user_media_pm(self, client: Client, message: Message):
        user = message.from_user
        if not user or message.outgoing:
            return

        # Check if the message contains any media
        if any([message.document, message.video, message.audio, message.voice, message.photo, message.video_note]):
            # Wait for the configured time (AUTO_DEL) or default to 4 hours
            wait_time = self.auto_del if self.auto_del > 0 else 14400
            await asyncio.sleep(wait_time)
            try:
                await message.delete()
                # self.LOGGER(__name__, self.name).info(f"Auto-deleted media from user {user.id} in PM.")
            except Exception as e:
                pass

    async def start(self):
        # --- Register the Auto-Delete Handler ---
        self.add_handler(
            MessageHandler(
                self.auto_delete_user_media_pm, 
                filters.private & ~filters.service
            )
        )
        
        # --- FloodWait Protection ---
        try:
            await super().start()
        except FloodWait as e:
            self.LOGGER(__name__, self.name).warning(f"⚠️ FloodWait triggered: Waiting for {e.value} seconds...")
            await asyncio.sleep(e.value)
            await super().start()
        except Exception as e:
            self.LOGGER(__name__, self.name).error(f"Failed to start client: {e}")
            sys.exit(1)

        usr_bot_me = await self.get_me()
        self.uptime = datetime.now()
        self.username = usr_bot_me.username

        # --- Load Settings from MongoDB ---
        saved_settings = await self.mongodb.load_settings(self.name)
        if saved_settings:
            self.LOGGER(__name__, self.name).info("Found saved settings in database. Loading them.")
            self.admins = saved_settings.get("admins", self.admins)
            self.messages = saved_settings.get("messages", self.messages)
            self.auto_del = saved_settings.get("auto_del", self.auto_del)
            self.protect = saved_settings.get("protect", self.protect)
            self.disable_btn = saved_settings.get("disable_btn", self.disable_btn)
            self.reply_text = saved_settings.get("reply_text", self.reply_text)
            self.fsub = saved_settings.get("fsub", self.fsub)
        else:
            self.LOGGER(__name__, self.name).info("No saved settings found. Using initial config from setup.json.")

        # --- Initialize Force Sub Channels ---
        self.fsub_dict = {}
        if len(self.fsub) > 0:
            for channel in self.fsub:
                try:
                    chat = await self.get_chat(channel[0])
                    name = chat.title
                    link = None
                    
                    if not channel[1]: 
                        try:
                           link = chat.invite_link
                        except AttributeError:
                           pass
                    
                    if not link:
                        if channel[2] <= 0 or channel[1]:
                            try:
                                chat_link = await self.create_chat_invite_link(channel[0], creates_join_request=channel[1])
                                link = chat_link.invite_link
                            except Exception as e:
                                self.LOGGER(__name__, self.name).error(f"Failed to create invite link: {e}")
                                link = None

                    if name:
                        self.fsub_dict[channel[0]] = [name, link, channel[1], channel[2]]
                    
                    if channel[1]:
                        self.req_channels.append(channel[0])

                except Exception as e:
                    self.LOGGER(__name__, self.name).warning(f"Bot can't Export Invite link from Force Sub Channel {channel[0]}! Error: {e}")
            
            if self.req_channels:
                await self.mongodb.set_channels(self.req_channels)

        # --- Check Access for ALL DB Channels ---
        for db_id in self.db_channels:
            try:
                chat = await self.get_chat(db_id)
                # We send a test message to ensure we have Write Access
                test = await self.send_message(chat_id=db_id, text=f"Bot Connected: @{self.username}")
                await test.delete()
            except Exception as e:
                self.LOGGER(__name__, self.name).error(f"⚠️ Error accessing DB Channel {db_id}: {e}")
                self.LOGGER(__name__, self.name).error("Make sure bot is Admin in ALL DB channels.")

        self.LOGGER(__name__, self.name).info(f"Bot @{self.username} Started!!")

    async def stop(self, *args):
        await super().stop()
        self.LOGGER(__name__, self.name).info("Bot stopped.")


async def web_app():
    # ensure plugins.web_server returns a web.Application
    app = web.AppRunner(await web_server()) 
    await app.setup()
    bind_address = "0.0.0.0"
    # Ensure PORT is an integer
    await web.TCPSite(app, bind_address, int(PORT)).start()
