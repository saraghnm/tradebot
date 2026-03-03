# bot.py

import time
import threading
import core.trader as trader_module
from core.notifier import notify, get_updates
from core.trader import startup_check, active_trades, get_price
from core.scheduler import start_scheduler
from core.stream import start_stream
from commands import handle_message


def resume_trades():
    from core.trader import monitor_trade
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
                trade.get("take_profit1"),
                trade.get("take_profit2"),
            )
        )
        thread.daemon = True
        thread.start()
    if active_trades:
        notify(f"▶️ Resumed {len(active_trades)} active trade(s) from last session!")


def resume_alerts():
    from core.trader import monitor_alert, active_alerts
    for symbol, alert in active_alerts.items():
        print(f"🔔 Resuming alert: {symbol}")
        thread = threading.Thread(
            target=monitor_alert,
            args=(
                symbol,
                alert["target_price"],
                alert["amount"],
                alert.get("custom_stop_price"),
            )
        )
        thread.daemon = True
        thread.start()
    if active_alerts:
        notify(f"🔔 Resumed {len(active_alerts)} active alert(s) from last session!")


def refresh_stream():
    symbols = list(active_trades.keys())
    if symbols:
        start_stream(symbols)


# Startup
startup_check()
resume_trades()
resume_alerts()
refresh_stream()

# Start scheduler
daily_pnl_ref = [trader_module.daily_pnl]
start_scheduler(active_trades, daily_pnl_ref, get_price)

notify("🤖 Bot is online! Send 'help' for available commands")

# Skip old messages on startup
initial_updates = get_updates()
if initial_updates.get("result"):
    offset = initial_updates["result"][-1]["update_id"] + 1
else:
    offset = None

# Main loop
while True:
    try:
        updates = get_updates(offset)
        for update in updates.get("result", []):
            offset = update["update_id"] + 1
            message = update.get("message", {})
            text = message.get("text", "")
            if text:
                print(f"📩 Received: {text}")
                handle_message(text)
    except Exception as e:
        print(f"⚠️ Main loop error: {e}")
    time.sleep(1)