import os
import logging
from logging.handlers import RotatingFileHandler

# ================================================================
#  SECURE & STABLE BOT CONFIG
#  Works even if environment variables are missing/empty.
# ================================================================

def env_int(key, default):
    """Safely read integer environment variables."""
    val = os.getenv(key)
    return int(val) if val and val.isdigit() else default

def env_str(key, default):
    """Safely read string environment variables."""
    val = os.getenv(key)
    return val if val not in (None, "", " ") else default


# ------------------  CORE BOT CREDENTIALS  ----------------------

API_ID = env_int("API_ID", 2468192)
API_HASH = env_str("API_HASH", "4906b3f8f198ec0e24edb2c197677678")
BOT_TOKEN = env_str("BOT_TOKEN", "7845953013:AAF-GS-0IRyCcxAHx9JPXSWqvXypM3J6ZRE")
SESSION = env_str("SESSION", "Codeflixold")


# ------------------  DATABASE CONFIG  ---------------------------

DB_URI = env_str(
    "DB_URI",
    "mongodb+srv://Filter01:ei62heT4O81OyNyl@Filter01.6kyybcz.mongodb.net/?retryWrites=true&w=majority&appName=Filter01"
)

DB_NAME = env_str("DB_NAME", "Codeflixold")


# ------------------  SERVER / WORKERS ---------------------------

PORT = env_int("PORT", 8080)
WORKERS = env_int("TG_BOT_WORKERS", 4)


# ------------------  OWNER & ADMINS  ----------------------------

OWNER_ID = env_int("OWNER_ID", 2098589219)
ADMINS = [OWNER_ID]


# ------------------  FORCE SUBSCRIPTION -------------------------

# Format → [channel_id, enabled, timer_minutes]
FSUBS = [
    [-1001910769204, True, 60],
]


# ------------------  DATABASE CHANNEL ---------------------------

DB_CHANNEL = env_str("DB_CHANNEL", "-1002093620952, -1001683081282")


# ------------------  AUTO DELETE TIMER --------------------------

AUTO_DEL = env_int("AUTO_DEL", 14400)  # 4 hours


# ------------------  PROTECTION FLAGS ---------------------------

DISABLE_BTN = bool(env_int("DISABLE_BTN", 1))
PROTECT = bool(env_int("PROTECT", 1))


# ------------------  OTHER CONFIGS ------------------------------

MSG_EFFECT = env_int("MSG_EFFECT", 5046509860389126442)


# ================================================================
#  MESSAGE TEMPLATES
# ================================================================

MESSAGES = {
    "START": (
        "<b>›› ʜᴇʏ!!, {first} ~ "
        "<blockquote>ʟᴏᴠᴇ ᴘᴏʀɴʜᴡᴀ? ɪ ᴀᴍ ᴍᴀᴅᴇ ᴛᴏ ʜᴇʟᴘ ʏᴏᴜ ᴛᴏ ғɪɴᴅ ᴡʜᴀᴛ ʏᴏᴜ aʀᴇ ʟᴏᴏᴋɪɴɢ ꜰᴏʀ.</blockquote></b>"
    ),
    "FSUB": "<b>Join This Channels For Get Videos/Files👇👇</b>",
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
    "FSUB_PHOTO": "https://envs.sh/etM.jpg",
}


# ================================================================
#  LOGGING SETUP
# ================================================================

LOG_FILE_NAME = "bot.log"

def LOGGER(name: str, client_name: str) -> logging.Logger:
    """Creates/retrieves logger with rotation and safe handler setup."""
    logger = logging.getLogger(name)

    if logger.handlers:
        return logger

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
