Import asyncio
import json
import sys
from bot import Bot, web_app
from pyrogram import compose

# Static default fallback message templates
default_messages = {
    'START': '<blockquote expandable>__Lorem ipsum dolor sit amet,\nconsectetur adipiscing elit sed.\nVivamus luctus urna sed urna.\nCurabitur blandit tempus porttitor.\nNullam quis risus eget urna.__</blockquote>',
    'FSUB': '',
    'ABOUT': 'ABOUT MSG',
    'REPLY': 'reply_text',
    'START_PHOTO': '',
    'FSUB_PHOTO': ''
}

async def main():
    app = []

    # Load setup.json
    try:
        with open("setup.json", "r") as f:
            setups = json.load(f)
    except FileNotFoundError:
        print("❌ Error: setup.json file not found!")
        return
    except json.JSONDecodeError:
        print("❌ Error: setup.json is not a valid JSON file. Please check for syntax errors.")
        return

    # Loop through each bot setup config
    for i, config in enumerate(setups):
        session = config.get("session", f"Bot_{i}")
        
        # --- Validation Checks ---
        api_id_raw = config.get("api_id")
        token = config.get("token")

        if not api_id_raw:
            print(f"⚠️ SKIPPING Bot '{session}': API_ID is missing or empty in setup.json.")
            continue
            
        if not token:
            print(f"⚠️ SKIPPING Bot '{session}': Bot Token is missing in setup.json.")
            continue

        try:
            api_id = int(api_id_raw)
        except ValueError:
            print(f"⚠️ SKIPPING Bot '{session}': API_ID '{api_id_raw}' is not a number.")
            continue
        # ------------------------------

        # Safely get other variables with defaults if needed
        workers = config.get("workers", 4)
        db = config.get("db")
        fsubs = config.get("fsubs", {})
        admins = config.get("admins", [])
        messages = config.get("messages", default_messages)
        auto_del = config.get("auto_del", 0)
        db_uri = config.get("db_uri")
        db_name = config.get("db_name")
        api_hash = config.get("api_hash")
        protect = config.get("protect", False)
        disable_btn = config.get("disable_btn", False)

        if not api_hash:
             print(f"⚠️ SKIPPING Bot '{session}': API_HASH is missing.")
             continue

        app.append(
            Bot(
                session,
                workers,
                db,
                fsubs,
                token,
                admins,
                messages,
                auto_del,
                db_uri,
                db_name,
                api_id,
                api_hash,
                protect,
                disable_btn
            )
        )

    if not app:
        print("❌ No valid bot configurations found. Exiting.")
        sys.exit(1)

    print(f"✅ Starting {len(app)} bot(s)...")
    
    # compose() handles starting all clients and idling
    await compose(app)


async def runner():
    # Run the bot manager (main) and the web server (web_app) concurrently
    await asyncio.gather(
        main(),
        web_app()
    )

if __name__ == "__main__":
    try:
        asyncio.run(runner())
    except KeyboardInterrupt:
        print("Bot stopped by user.")
