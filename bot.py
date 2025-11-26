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
        
        # --- Handle Multiple Database Channels ---
        self.db_channels = []
        try:
            if isinstance(db, list):
                self.db_channels = [int(x) for x in db]
            elif isinstance(db, str):
                if "," in db:
                    self.db_channels = [int(x.strip()) for x in db.split(",") if x.strip().lstrip("-").isdigit()]
                else:
                    self.db_channels = [int(db)]
            else:
                self.db_channels = [int(db)]
        except Exception as e:
            self.LOGGER(__name__, self.name).warning(f"DB Channel ID format warning: {e}")
            if isinstance(db, list):
                self.db_channels = db
            else:
                self.db_channels = [db]

        # Set the PRIMARY DB (The first one)
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
        
        self.mongodb = MongoDB(db_uri, db_name)
        self.req_channels = []
    
    def get_current_settings(self):
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

        if any([message.document, message.video, message.audio, message.voice, message.photo, message.video_note]):
            # Wait for AUTO_DEL time (default 4 hours)
            wait_time = self.auto_del if self.auto_del > 0 else 14400
            await asyncio.sleep(wait_time)
            try:
                await message.delete()
            except Exception:
                pass

    async def start(self):
        # --- Register Handler in GROUP 10 (Fixes Conflict) ---
        self.add_handler(
            MessageHandler(
                self.auto_delete_user_media_pm, 
                filters.private & ~filters.service
            ),
            group=10
        )
        
        try:
            await super().start()
        except FloodWait as e:
            self.LOGGER(__name__, self.name).warning(f"⚠️ FloodWait: Waiting {e.value}s...")
            await asyncio.sleep(e.value)
            await super().start()
        except Exception as e:
            self.LOGGER(__name__, self.name).error(f"Failed to start client: {e}")
            sys.exit(1)

        usr_bot_me = await self.get_me()
        self.uptime = datetime.now()
        self.username = usr_bot_me.username

        # --- Load Settings ---
        saved_settings = await self.mongodb.load_settings(self.name)
        if saved_settings:
            self.LOGGER(__name__, self.name).info("Found saved settings in database.")
            self.admins = saved_settings.get("admins", self.admins)
            self.messages = saved_settings.get("messages", self.messages)
            self.auto_del = saved_settings.get("auto_del", self.auto_del)
            self.protect = saved_settings.get("protect", self.protect)
            self.disable_btn = saved_settings.get("disable_btn", self.disable_btn)
            self.reply_text = saved_settings.get("reply_text", self.reply_text)
            self.fsub = saved_settings.get("fsub", self.fsub)
        else:
            self.LOGGER(__name__, self.name).info("Using config.py settings.")

        # --- Initialize FSubs ---
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
                            except Exception:
                                link = None

                    if name:
                        self.fsub_dict[channel[0]] = [name, link, channel[1], channel[2]]
                    
                    if channel[1]:
                        self.req_channels.append(channel[0])

                except Exception as e:
                    self.LOGGER(__name__, self.name).warning(f"FSub Error {channel[0]}: {e}")
            
            if self.req_channels:
                await self.mongodb.set_channels(self.req_channels)

        # --- Check DB Channels ---
        for db_id in self.db_channels:
            try:
                chat = await self.get_chat(db_id)
                test = await self.send_message(chat_id=db_id, text=f"Bot Connected: @{self.username}")
                await test.delete()
            except Exception as e:
                self.LOGGER(__name__, self.name).error(f"⚠️ DB Channel Error {db_id}: {e}")

        self.LOGGER(__name__, self.name).info(f"Bot @{self.username} Started!!")

    async def stop(self, *args):
        await super().stop()
        self.LOGGER(__name__, self.name).info("Bot stopped.")


async def web_app():
    app = web.AppRunner(await web_server()) 
    await app.setup()
    bind_address = "0.0.0.0"
    await web.TCPSite(app, bind_address, int(PORT)).start()
