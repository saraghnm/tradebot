# bot.py

import time
from notifier import notify, get_updates
from trader import startup_check, active_trades
from commands import handle_message
import threading


def resume_trades():
    from trader import monitor_trade
    for symbol, trade in active_trades.items():
        print(f"▶️ Resuming trade: {symbol}")
        thread = threading.Thread(
            target=monitor_trade,
            args=(
                symbol,
                trade["quantity"],
                trade["entry_price"],
                trade["investment"],
                trade.get("custom_stop_price"),
            )
        )
        thread.daemon = True
        thread.start()
    if active_trades:
        notify(f"▶️ Resumed {len(active_trades)} active trade(s) from last session!")


# Startup check
startup_check()

# Resume any active trades from last session
resume_trades()

# Notify bot is online
notify("🤖 Bot is online! Send 'help' for available commands")

# Skip old messages on startup
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
            print(f"📩 Received: {text}")
            handle_message(text)
    time.sleep(1)