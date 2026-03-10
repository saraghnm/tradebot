# core/scheduler.py

import time
import threading
from datetime import datetime
from core.notifier import notify
from core.history import get_stats


def midnight_reset(get_price_fn):
    import core.trader as trader_module
    from core.state import save_state

    while True:
        try:
            now = datetime.now()
            if now.hour == 0 and now.minute == 0:
                active_trades = trader_module.active_trades
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

💰 Realized P/L: ${trader_module.daily_pnl:.4f}
📊 Unrealized P/L: ${unrealized:.4f}
🔄 Active trades: {active_count}"""

                if stats:
                    msg += f"""

📈 All-time stats:
Total trades: {stats['total']}
Win rate: {stats['win_rate']:.1f}%
Total profit: ${stats['total_profit']}"""

                notify(msg)

                # Reset daily P/L directly in the module + persist it
                trader_module.daily_pnl = 0.0
                save_state(trader_module.active_trades, 0.0, trader_module.active_alerts)
                notify("🔄 Daily P/L reset for new day!")

                # Sleep 61 seconds to avoid double trigger
                time.sleep(61)

        except Exception as e:
            notify(f"⚠️ Scheduler error: {e}")

        time.sleep(30)


def start_scheduler(active_trades, daily_pnl_ref, get_price_fn):
    thread = threading.Thread(
        target=midnight_reset,
        args=(get_price_fn,)
    )
    thread.daemon = True
    thread.start()