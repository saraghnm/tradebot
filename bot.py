# bot.py

import time
from logger import log
from notifier import notify, get_updates
from trader import startup_check
from commands import handle_message


# Startup check
startup_check()

# Test Telegram
notify("🤖 Bot is online! Send 'help' for available commands")
log("🤖 Bot is running!", type="monitor")

# Skip old messages on startup
log("Skipping old messages...", type="monitor")
initial_updates = get_updates()
if initial_updates.get("result"):
    offset = initial_updates["result"][-1]["update_id"] + 1
else:
    offset = None

# Main loop
while True:
    updates = get_updates(offset)
    for update in updates.get("result", []):
        offset = update["update_id"] + 1
        message = update.get("message", {})
        text = message.get("text", "")
        if text:
            log(f"📩 Received: {text}", type="monitor")
            handle_message(text)
    time.sleep(1)