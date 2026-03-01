# commands.py

import threading
from config import settings
from notifier import notify
from trader import (
    active_trades,
    daily_pnl,
    client,
    get_price,
    get_lot_size,
    buy,
    sell,
    monitor_trade,
)


def handle_message(text):
    global daily_pnl
    parts = text.strip().split()
    command = parts[0].lower()

    # BUY
    if len(parts) >= 3 and command == "buy":
        symbol = parts[1].upper() + "USDT"
        if symbol in active_trades:
            notify(f"⚠️ Already monitoring {parts[1].upper()}!\nSell it first before buying again.")
            return
        if daily_pnl <= settings["daily_loss_limit"]:
            notify(f"🚫 Daily loss limit reached! No more trades today.\nDaily P/L: ${daily_pnl:.4f}")
            return
        try:
            amount = float(parts[2])
            custom_stop = float(parts[3]) if len(parts) == 4 else None
            notify(f"📩 Order received!\nBuying ${amount} of {parts[1].upper()}")
            quantity, entry_price = buy(symbol, amount)
            thread = threading.Thread(
                target=monitor_trade, args=(symbol, quantity, entry_price, amount, custom_stop)
            )
            thread.daemon = True
            thread.start()
        except Exception as e:
            notify(f"❌ Error: {e}")

    # SELL
    elif command == "sell" and len(parts) > 1:
        symbol = parts[1].upper() + "USDT"
        try:
            account = client.get_account()
            balance = next(
                (float(a["free"]) for a in account["balances"] if a["asset"] == parts[1].upper()), 0
            )
            if balance > 0:
                step_size = get_lot_size(symbol)
                precision = len(str(step_size).rstrip("0").split(".")[-1])
                quantity = round(balance - (balance % step_size), precision)
                sell(symbol, quantity)
                active_trades.pop(symbol, None)
                notify(f"🔴 Force sell executed!\n{parts[1].upper()} sold: {quantity}")
            else:
                notify(f"❌ No {parts[1].upper()} balance to sell!")
        except Exception as e:
            notify(f"❌ Error: {e}")

    # PRICE
    elif command == "price" and len(parts) > 1:
        symbol = parts[1].upper() + "USDT"
        try:
            price = get_price(symbol)
            notify(f"💲 {parts[1].upper()} Price: ${price:,.4f}")
        except Exception as e:
            notify(f"❌ Error: {e}")

    # BALANCE
    elif command == "balance":
        try:
            account = client.get_account()
            balances = [
                f"{a['asset']}: {a['free']}"
                for a in account["balances"]
                if float(a["free"]) > 0
            ]
            notify("💰 Your balances:\n" + "\n".join(balances[:20]))
        except Exception as e:
            notify(f"❌ Error: {e}")

    # ORDERS
    elif command == "orders" and len(parts) > 1:
        try:
            orders = client.get_all_orders(symbol=parts[1].upper() + "USDT")
            if orders:
                msg = "\n".join(
                    [f"{o['side']} {o['origQty']} @ {o['price']} - {o['status']}" for o in orders[-5:]]
                )
                notify(f"📋 Last 5 orders:\n{msg}")
            else:
                notify(f"No orders found for {parts[1].upper()}")
        except Exception as e:
            notify(f"❌ Error: {e}")

    # STATUS
    elif command == "status":
        try:
            if active_trades:
                msg = ""
                for symbol, trade in active_trades.items():
                    current_price = get_price(symbol)
                    current_value = trade["quantity"] * current_price
                    profit = current_value - trade["investment"]
                    stop_info = f"\nStop: ${trade['custom_stop_price']}" if trade.get("custom_stop_price") else ""
                    msg += f"📊 {symbol}\nEntry: ${trade['entry_price']:,.4f}\nCurrent: ${current_price:,.4f}\nP/L: ${profit:.4f}{stop_info}\n\n"
                notify(f"📊 Active trades:\n{msg}Daily P/L: ${daily_pnl:.4f}")
            else:
                notify(f"No active trades\nDaily P/L: ${daily_pnl:.4f}")
        except Exception as e:
            notify(f"❌ Error: {e}")

    # SET
    elif command == "set" and len(parts) == 3:
        key = parts[1].lower()
        if key in settings:
            try:
                settings[key] = float(parts[2])
                notify(f"⚙️ Updated {key} to {parts[2]}")
            except Exception:
                notify(f"❌ Invalid value for {key}")
        else:
            notify(f"❌ Unknown setting: {key}\nAvailable: {', '.join(settings.keys())}")
    
    # SET STOP
    elif command == "setstop" and len(parts) == 3:
        symbol = parts[1].upper() + "USDT"
        if symbol in active_trades:
            try:
                new_stop = float(parts[2])
                active_trades[symbol]["custom_stop_price"] = new_stop
                from state import save_state
                from trader import daily_pnl
                save_state(active_trades, daily_pnl)
                notify(f"✅ Stop loss updated!\n{parts[1].upper()} new stop: ${new_stop}")
            except Exception as e:
                notify(f"❌ Error: {e}")
        else:
            notify(f"❌ {parts[1].upper()} is not an active trade!")
    # ALERT
    elif command == "alert" and len(parts) >= 3:
        symbol = parts[1].upper() + "USDT"
        if symbol in active_trades:
            notify(f"⚠️ Already monitoring {parts[1].upper()}!\nSell it first before setting an alert.")
            return
        try:
            target_price = float(parts[2])
            amount = float(parts[3]) if len(parts) >= 4 else 10.0
            custom_stop = float(parts[4]) if len(parts) == 5 else None
            from trader import monitor_alert
            thread = threading.Thread(
                target=monitor_alert,
                args=(symbol, target_price, amount, custom_stop)
            )
            thread.daemon = True
            thread.start()
            notify(f"🔔 Alert created!\n{parts[1].upper()} → buy at ${target_price}\nAmount: ${amount}\nStop: ${custom_stop if custom_stop else 'default'}")
        except Exception as e:
            notify(f"❌ Error: {e}")
            
    # SUMMARY
    elif command == "summary":
        notify(
            f"📈 Daily Trade Summary\nTotal P/L: ${daily_pnl:.4f}\nActive trades: {len(active_trades)}\nSettings:\n"
            + "\n".join([f"  {k}: {v}" for k, v in settings.items()])
        )

    # HELP
    elif command == "help":
        notify(
            """🤖 zTrading Bot Commands

🪙 TRADING:
- buy COIN 10 → buy $10 of a COIN
- buy COIN 10 0.085 → buy with stop loss price
- sell COIN → force sell a COIN
- setstop COIN 0.085 → update stop loss
- alert COIN 1.70 10 1.60 → buy when price hits 1.70

📊 MONITORING:
- price COIN → current price for a COIN
- status → active trades & P/L
- summary → daily summary
- balance → wallet balances
- orders COIN → last 5 orders

⚙️ SETTINGS:
- set min_profit 1.5
- set trail_amount 0.50
- set hard_stop_loss -1.0
- set daily_loss_limit -10.0

❓ help → show this message"""
        )

    else:
        notify("❓ Unknown command! Send 'help' for available commands.")