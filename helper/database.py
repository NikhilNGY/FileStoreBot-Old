import motor.motor_asyncio
from datetime import datetime

class MongoDB:
    def __init__(self, uri, database_name):
        # 1. Initialize Client and DB
        self.client = motor.motor_asyncio.AsyncIOMotorClient(uri)
        self.db = self.client[database_name]

        # 2. Initialize Collections
        self.col = self.db.short_links          # For file links
        self.user_data = self.db.users          # For user stats/bans
        self.channel_data = self.db.channels    # For channel management
        self.bot_settings = self.db.bot_settings # For bot settings

    # --- File Link Methods ---

    def new_file(self, file_id, from_id, to_id=None):
        """Creates the dictionary structure for the database."""
        return {
            "file_id": file_id,
            "from_id": from_id,
            "to_id": to_id,
            "created_at": datetime.now()
        }

    async def add_file(self, file_id, from_id, to_id=None):
        """Saves the generated file_id mapping to MongoDB."""
        file_data = self.new_file(file_id, from_id, to_id)
        try:
            await self.col.insert_one(file_data)
            return True
        except Exception as e:
            print(f"Error saving to DB: {e}")
            return False

    async def get_file(self, file_id):
        """Retrieves the message IDs using the file_id."""
        try:
            file_data = await self.col.find_one({"file_id": file_id})
            return file_data
        except Exception as e:
            print(f"Error getting from DB: {e}")
            return None

    # --- Settings Methods ---

    async def save_settings(self, session_name: str, settings: dict):
        """Saves the bot's settings to the database."""
        await self.bot_settings.update_one(
            {"_id": session_name},
            {"$set": {"settings": settings}},
            upsert=True
        )

    async def load_settings(self, session_name: str) -> dict | None:
        """Loads the bot's settings from the database."""
        data = await self.bot_settings.find_one({"_id": session_name})
        return data.get("settings") if data else None

    # --- Channel Methods ---
    
    async def set_channels(self, channels: list[int]):
        await self.user_data.update_one(
            {"_id": 1},
            {"$set": {"channels": channels}},
            upsert=True
        )
    
    async def get_channels(self) -> list[int]:
        data = await self.user_data.find_one({"_id": 1})
        return data.get("channels", []) if data else []
    
    async def add_channel_user(self, channel_id: int, user_id: int):
        await self.channel_data.update_one(
            {"_id": channel_id},
            {"$addToSet": {"users": user_id}},  # $addToSet avoids duplicates automatically
            upsert=True
        )

    async def remove_channel_user(self, channel_id: int, user_id: int):
        await self.channel_data.update_one(
            {"_id": channel_id},
            {"$pull": {"users": user_id}}
        )

    async def get_channel_users(self, channel_id: int) -> list[int]:
        doc = await self.channel_data.find_one({"_id": channel_id})
        return doc.get("users", []) if doc else []
        
    async def is_user_in_channel(self, channel_id: int, user_id: int) -> bool:
        doc = await self.channel_data.find_one(
            {"_id": channel_id, "users": {"$in": [user_id]}},
            {"_id": 1}  # minimize fetched data for speed
        )
        return doc is not None

    # --- User Management Methods ---

    async def present_user(self, user_id: int) -> bool:
        found = await self.user_data.find_one({'_id': user_id})
        return bool(found)

    async def add_user(self, user_id: int, ban: bool = False):
        # Use update_one with upsert=True to prevent errors if user already exists
        await self.user_data.update_one(
            {'_id': user_id},
            {'$setOnInsert': {'ban': ban}},
            upsert=True
        )

    async def full_userbase(self) -> list[int]:
        user_docs = self.user_data.find()
        return [doc['_id'] async for doc in user_docs]

    async def del_user(self, user_id: int):
        await self.user_data.delete_one({'_id': user_id})

    async def ban_user(self, user_id: int):
        await self.user_data.update_one({'_id': user_id}, {'$set': {'ban': True}})

    async def unban_user(self, user_id: int):
        await self.user_data.update_one({'_id': user_id}, {'$set': {'ban': False}})

    async def is_banned(self, user_id: int) -> bool:
        user = await self.user_data.find_one({'_id': user_id})
        return user.get('ban', False) if user else False
