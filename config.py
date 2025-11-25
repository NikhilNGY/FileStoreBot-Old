import os
import logging
from logging.handlers import RotatingFileHandler

# ================================================================
#  Secure Bot Configuration
#  Environment variables should be set in your hosting dashboard.
# ================================================================

# Core Bot Credentials
API_ID = int(os.getenv("APP_ID", 2468192))
API_HASH = os.getenv("API_HASH", "4906b3f8f198ec0e24edb2c197677678")
BOT_TOKEN = os.getenv("BOT_TOKEN", "7845953013:AAEYbYFSCkC6IuGy9yrUz1E56EFmtge_jQs")
SESSION = os.getenv("SESSION", "Codeflixold")

# Database Configuration
DB_URI = os.getenv(
    "DB_URI",
    "mongodb+srv://Filter01:ei62heT4O81OyNyl@Filter01.6kyybcz.mongodb.net/?retryWrites=true&w=majority&appName=Filter01"
)
DB_NAME = os.getenv("DB_NAME", "Codeflixold")

# Server Configuration
PORT = int(os.getenv("PORT", 8080))
WORKERS = int(os.getenv("TG_BOT_WORKERS", 4))

# Owner & Admins
OWNER_ID = int(os.getenv("OWNER_ID", 2098589219))
ADMINS = [OWNER_ID]

# Force Subscription Settings: [channel_id, enabled, timer_in_minutes]
FSUBS = [
    [-1001910769204, True, 60],
]

# Database Channel
DB_CHANNEL = os.getenv("DB_CHANNEL", "-1002093620952")

# Auto Delete Timer (seconds)
AUTO_DEL = int(os.getenv("AUTO_DEL", 14400))

# Protection Settings
DISABLE_BTN = bool(int(os.getenv("DISABLE_BTN", 1)))   # 1 = True, 0 = False
PROTECT = bool(int(os.getenv("PROTECT", 1)))           # 1 = True, 0 = False

# Other Configurations
MSG_EFFECT = int(os.getenv("MSG_EFFECT", 5046509860389126442))

# ================================================================
#  Message Templates
# ================================================================

MESSAGES = {
    "START": (
        "<b>›› ʜᴇʏ!!, {first} ~ "
        "<blockquote>ʟᴏᴠᴇ ᴘᴏʀɴʜᴡᴀ? ɪ ᴀᴍ ᴍᴀᴅᴇ ᴛᴏ ʜᴇʟᴘ ʏᴏᴜ ᴛᴏ ғɪɴᴅ ᴡʜᴀᴛ ʏᴏᴜ aʀᴇ ʟᴏᴏᴋɪɴɢ ꜰᴏʀ.</blockquote></b>"
    ),
    "FSUB": (
        "<b>Join This Channels For Get Videos/Files👇👇</b>"
    ),
    "ABOUT": (
        "<b>›› ғᴏʀ ᴍᴏʀᴇ: @linkz_ki_duniyaa \n"
        "<blockquote expandable>›› ᴜᴘᴅᴀᴛᴇs ᴄʜᴀɴɴᴇʟ: "
        "<a href='https://t.me/linkz_ki_duniyaa'>Cʟɪᴄᴋ ʜᴇʀᴇ</a> \n"
        "›› ᴏᴡɴᴇʀ: @Sandalwood_Man \n"
        "›› ʟᴀɴɢᴜᴀɢᴇ: Pʏᴛʜᴏɴ 3 \n"
        "›› ʟɪʙʀᴀʀʏ: Pʏʀᴏɢʀᴀᴍ ᴠ2 \n"
        "›› ᴅᴀᴛᴀʙᴀsᴇ: Mᴏɴɢᴏ ᴅʙ \n"
        "›› ᴅᴇᴠᴇʟᴏᴘᴇʀ: @Sandalwood_Man</b></blockquote>"
    ),
    "REPLY": "<b>For More Join - @linkz_ki_duniyaa</b>",
    "START_PHOTO": "https://envs.sh/gz3.jpg",
    "FSUB_PHOTO": "https://envs.sh/etM.jpg"
}

# ================================================================
#  Logging Setup
# ================================================================

LOG_FILE_NAME = "bot.log"

def LOGGER(name: str, client_name: str) -> logging.Logger:
    """
    Creates or returns a configured logger with rotation.
    Prevents duplicate handlers on multiple imports.
    """
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger  # Prevent duplicate logs

    formatter = logging.Formatter(
        f"[%(asctime)s - %(levelname)s] - {client_name} - %(name)s - %(message)s",
        datefmt='%d-%b-%y %H:%M:%S'
    )

    file_handler = RotatingFileHandler(LOG_FILE_NAME, maxBytes=50_000_000, backupCount=10)
    file_handler.setFormatter(formatter)

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)

    logger.setLevel(logging.INFO)
    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)

    return logger
