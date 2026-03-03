# core/scheduler.py

import time
import threading
from datetime import datetime
from core.notifier import notify
from core.history import get_stats


def midnight_reset(active_trades, daily_pnl_ref, get_price_fn):
    while True:
        try:
            now = datetime.now()
            if now.hour == 0 and now.minute == 0:
                stats = get_stats()
                active_count = len(active_trades)

                # Calculate unrealized P/L
                unrealized = 0
                for symbol, trade in active_trades.items():
                    try:
                        current_price = get_price_fn(symbol)
                        current_value = trade["quantity"] * current_price
                        unrealized += current_value - trade["investment"]
                    except Exception as e:
                        notify(f"⚠️ Could not fetch price for {symbol}: {e}")

                msg = f"""🌙 Daily Summary — {now.strftime('%Y-%m-%d')}

💰 Realized P/L: ${daily_pnl_ref[0]:.4f}
📊 Unrealized P/L: ${unrealized:.4f}
🔄 Active trades: {active_count}"""

                if stats:
                    msg += f"""

📈 All-time stats:
Total trades: {stats['total']}
Win rate: {stats['win_rate']:.1f}%
Total profit: ${stats['total_profit']}"""

                notify(msg)

                # Reset daily P/L
                daily_pnl_ref[0] = 0.0
                notify("🔄 Daily P/L reset for new day!")

                # Sleep 61 seconds to avoid double trigger
                time.sleep(61)

        except Exception as e:
            notify(f"⚠️ Scheduler error: {e}")

        time.sleep(30)


def start_scheduler(active_trades, daily_pnl_ref, get_price_fn):
    thread = threading.Thread(
        target=midnight_reset,
        args=(active_trades, daily_pnl_ref, get_price_fn)
    )
    thread.daemon = True
    thread.start()