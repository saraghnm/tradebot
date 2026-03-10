# commands.py

import threading
import core.trader as trader_module
from config import settings
from core.notifier import notify
from core.stream import start_stream
from core.trader import (
    active_trades,
    client,
    get_price,
    get_lot_size,
    buy,
    sell,
    monitor_trade,
    get_error_message,
)

# Always read daily_pnl live from the module — never use an imported copy
def get_daily_pnl():
    return trader_module.daily_pnl


def handle_message(text):
    parts = text.strip().split()
    command = parts[0].lower()

    # BUY
    if len(parts) >= 3 and command == "buy":
        symbol = parts[1].upper() + "USDT"
        if symbol in active_trades:
            notify(f"⚠️ Already monitoring {parts[1].upper()}!\nSell it first before buying again.")
            return
        if get_daily_pnl() <= settings["daily_loss_limit"]:
            notify(f"🚫 Daily loss limit reached! No more trades today.\nDaily P/L: ${get_daily_pnl():.4f}")
            return
        try:
            amount = float(parts[2])
            custom_stop = float(parts[3]) if len(parts) >= 4 else None
            take_profit1 = float(parts[4]) if len(parts) >= 5 else None
            take_profit2 = float(parts[5]) if len(parts) >= 6 else None
            notify(f"📩 Order received!\nBuying ${amount} of {parts[1].upper()}")
            quantity, entry_price = buy(symbol, amount)
            thread = threading.Thread(
                target=monitor_trade,
                args=(symbol, quantity, entry_price, amount, custom_stop, take_profit1, take_profit2),
            )
            thread.daemon = True
            thread.start()
            start_stream(list(active_trades.keys()))
        except Exception as e:
            notify(f"❌ Buy failed: {get_error_message(e)}")

   # SELL
    elif command == "sell" and len(parts) > 1:
        symbol = parts[1].upper() + "USDT"
        try:
            percent = float(parts[2]) if len(parts) > 2 else 100.0
            trade = active_trades.get(symbol)
            account = client.get_account()
            balance = next(
                (float(a["free"]) for a in account["balances"] if a["asset"] == parts[1].upper()), 0
            )
            if balance > 0:
                step_size = get_lot_size(symbol)
                precision = len(str(step_size).rstrip("0").split(".")[-1])
                
                # Calculate quantity based on percentage
                sell_quantity = balance * (percent / 100)
                sell_quantity = round(sell_quantity - (sell_quantity % step_size), precision)
                
                current_price = get_price(symbol)
                client.order_market_sell(symbol=symbol, quantity=sell_quantity)
                profit = (current_price - trade["entry_price"]) * sell_quantity if trade else 0
                
                # Only remove from active trades if selling 100%
                if percent >= 100:
                    from core.history import save_trade
                    if trade:
                        save_trade(symbol, trade["entry_price"], current_price, trade["investment"], profit, "Manual sell")
                    active_trades.pop(symbol, None)
                    notify(f"🔴 Sold 100% of {parts[1].upper()}\nQuantity: {sell_quantity}\nP/L: ${profit:.4f}")
                else:
                    notify(f"🔴 Sold {percent}% of {parts[1].upper()}\nQuantity: {sell_quantity}\nP/L: ${profit:.4f}\n💰 Remaining: {balance - sell_quantity:.4f}")
            else:
                notify(f"❌ No {parts[1].upper()} balance to sell!")
        except Exception as e:
            notify(f"❌ Sell failed: {get_error_message(e)}")

    # PRICE
    elif command == "price" and len(parts) > 1:
        symbol = parts[1].upper() + "USDT"
        try:
            price = get_price(symbol)
            notify(f"💲 {parts[1].upper()} Price: ${price:,.4f}")
        except Exception as e:
            notify(f"❌ Price fetch failed: {get_error_message(e)}")

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
            notify(f"❌ Balance fetch failed: {get_error_message(e)}")

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
            notify(f"❌ Orders fetch failed: {get_error_message(e)}")

    # STATUS
    elif command == "status":
        try:
            from core.watcher import active_watchers
            daily_pnl = get_daily_pnl()
            msg = ""

            if active_trades:
                msg += "📊 Active Trades\n"
                for symbol, trade in active_trades.items():
                    current_price = get_price(symbol)
                    current_value = trade["quantity"] * current_price
                    profit = current_value - trade["investment"]
                    pnl_emoji = "🟢" if profit >= 0 else "🔴"
                    stop_info = f"\nStop: ${trade['custom_stop_price']}" if trade.get("custom_stop_price") else ""
                    tp1_info  = f"\nTP1:  ${trade['take_profit1']}"       if trade.get("take_profit1")      else ""
                    tp2_info  = f"\nTP2:  ${trade['take_profit2']}"       if trade.get("take_profit2")      else ""
                    msg += f"──────────────\n{symbol}\nEntry: ${trade['entry_price']:,.4f}\nNow:   ${current_price:,.4f}\n{pnl_emoji} P/L: ${profit:.4f}{stop_info}{tp1_info}{tp2_info}\n\n"
            else:
                msg += "📊 No active trades\n"

            if active_watchers:
                msg += "\n👁 Watching\n"
                for sym in active_watchers:
                    in_trade = "🔄 in trade" if sym in active_trades else "⏳ scanning"
                    msg += f"  {sym} — {in_trade}\n"
            else:
                msg += "\n👁 No active watchers\n"

            msg += f"\n💰 Daily P/L: ${daily_pnl:.4f}"
            notify(msg)
        except Exception as e:
            notify(f"❌ Status failed: {get_error_message(e)}")

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
                from core.state import save_state
                from core.trader import active_alerts
                save_state(active_trades, trader_module.daily_pnl, active_alerts)
                notify(f"✅ Stop loss updated!\n{parts[1].upper()} new stop: ${new_stop}")
            except Exception as e:
                notify(f"❌ Setstop failed: {get_error_message(e)}")
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
            from core.trader import monitor_alert
            thread = threading.Thread(
                target=monitor_alert, args=(symbol, target_price, amount, custom_stop)
            )
            thread.daemon = True
            thread.start()
            notify(f"🔔 Alert created!\n{parts[1].upper()} → buy at ${target_price}\nAmount: ${amount}\nStop: ${custom_stop if custom_stop else 'default'}")
        except Exception as e:
            notify(f"❌ Alert failed: {get_error_message(e)}")

    # ALERTS (view all)
    elif command == "alerts":
        from core.trader import active_alerts
        if active_alerts:
            msg = ""
            for symbol, alert in active_alerts.items():
                msg += f"🔔 {symbol}\nBuy at: ${alert['target_price']}\nAmount: ${alert['amount']}\nStop: ${alert['custom_stop_price'] if alert['custom_stop_price'] else 'default'}\n\n"
            notify(f"🔔 Active alerts:\n{msg}")
        else:
            notify("No active alerts")

    # CANCEL ALERT
    elif command == "cancelalert" and len(parts) > 1:
        from core.trader import active_alerts
        symbol = parts[1].upper() + "USDT"
        if symbol in active_alerts:
            active_alerts.pop(symbol, None)
            notify(f"🚫 Alert cancelled for {parts[1].upper()}")
        else:
            notify(f"❌ No active alert for {parts[1].upper()}")

    # TRACK
    elif command == "track" and len(parts) > 1:
        from core.trader import active_trackers, monitor_tracker
        symbol = parts[1].upper() + "USDT"
        percent = float(parts[2]) if len(parts) > 2 else 5.0
        if symbol in active_trackers:
            notify(f"⚠️ Already tracking {parts[1].upper()}!")
        else:
            active_trackers[symbol] = True
            thread = threading.Thread(target=monitor_tracker, args=(symbol, percent))
            thread.daemon = True
            thread.start()

    # UNTRACK
    elif command == "untrack" and len(parts) > 1:
        from core.trader import active_trackers
        symbol = parts[1].upper() + "USDT"
        if symbol in active_trackers:
            active_trackers.pop(symbol, None)
        else:
            notify(f"❌ Not tracking {parts[1].upper()}")

    # TRACKERS
    elif command == "trackers":
        from core.trader import active_trackers
        if active_trackers:
            notify("👀 Tracking:\n" + "\n".join(active_trackers.keys()))
        else:
            notify("No active trackers")

    # HISTORY
    elif command == "history":
        from core.history import get_history
        trades = get_history(10)
        if trades:
            msg = "📜 Last 10 trades:\n\n"
            for i, t in enumerate(reversed(trades), 1):
                emoji = "✅" if t["profit"] > 0 else "❌"
                msg += f"{emoji} {t['symbol']}\nEntry: ${t['entry_price']} | Exit: ${t['exit_price']}\nP/L: ${t['profit']} | {t['reason']}\n{t['date']}\n\n"
            notify(msg)
        else:
            notify("📜 No trade history yet!")

    # STATS
    elif command == "stats":
        from core.history import get_stats
        s = get_stats()
        if s:
            notify(f"""📈 Trading Stats

Total trades: {s['total']}
Wins: {s['wins']} | Losses: {s['losses']}
Win rate: {s['win_rate']:.1f}%
Total P/L: ${s['total_profit']}

🏆 Best: {s['best']['symbol']} +${s['best']['profit']}
💔 Worst: {s['worst']['symbol']} ${s['worst']['profit']}""")
        else:
            notify("📊 No stats yet — make some trades first!")

    # ANALYZE
    elif command == "analyze" and len(parts) > 1:
        symbol = parts[1].upper() + "USDT"
        try:
            notify(f"🤖 Analyzing {parts[1].upper()}...")
            from core.analyzer import analyze_coin
            analysis = analyze_coin(symbol)
            notify(f"📊 {parts[1].upper()} Analysis\n\n{analysis}")
        except Exception as e:
            notify(f"❌ Analysis failed: {get_error_message(e)}")

    # SUMMARY
    elif command == "summary":
        notify(
            f"📈 Daily Trade Summary\nTotal P/L: ${get_daily_pnl():.4f}\nActive trades: {len(active_trades)}\nSettings:\n"
            + "\n".join([f"  {k}: {v}" for k, v in settings.items()])
        )
# BUYA - Analyze before buy
    elif command == "buya" and len(parts) >= 3:
        symbol = parts[1].upper() + "USDT"
        if symbol in active_trades:
            notify(f"⚠️ Already monitoring {parts[1].upper()}!")
            return
        try:
            amount = float(parts[2])
            custom_stop = float(parts[3]) if len(parts) > 3 else None
            tp1 = float(parts[4]) if len(parts) > 4 else None
            tp2 = float(parts[5]) if len(parts) > 5 else None

            notify(f"🔍 Analyzing {parts[1].upper()} before buying...")

            def analyze_and_buy():
                from core.analyzer import analyze_coin
                analysis = analyze_coin(parts[1].upper())

                overall = ""
                for line in analysis.split("\n"):
                    if line.startswith("Overall:"):
                        overall = line.split(":", 1)[1].strip().lower()
                        break

                if "bullish" in overall:
                    notify(f"✅ Analysis: Bullish! Buying ${amount} of {parts[1].upper()}...\n\n{analysis}")
                    try:
                        quantity, entry_price = buy(symbol, amount)
                        thread = threading.Thread(
                            target=monitor_trade,
                            args=(symbol, quantity, entry_price, amount, custom_stop, tp1, tp2)
                        )
                        thread.daemon = True
                        thread.start()
                    except Exception as e:
                        notify(f"❌ Buy failed: {get_error_message(e)}")
                else:
                    notify(f"🚫 Analysis: {overall.capitalize()} — skipping buy.\n\n{analysis}")

            thread = threading.Thread(target=analyze_and_buy)
            thread.daemon = True
            thread.start()

        except Exception as e:
            notify(f"❌ Error: {get_error_message(e)}")
            
    # WATCH — start auto-trading a coin
    elif command == "watch" and len(parts) >= 3:
        from core.watcher import start_watcher, active_watchers
        symbol = parts[1].upper() + "USDT"
        try:
            amount      = float(parts[2])
            custom_stop = float(parts[3]) if len(parts) > 3 else None
            tp1         = float(parts[4]) if len(parts) > 4 else None
            tp2         = float(parts[5]) if len(parts) > 5 else None

            if symbol in active_watchers:
                notify(f"⚠️ Already watching {parts[1].upper()}!")
                return

            started = start_watcher(symbol, amount, custom_stop, tp1, tp2)
            if not started:
                notify(f"⚠️ Already watching {parts[1].upper()}!")
        except Exception as e:
            notify(f"❌ Watch failed: {get_error_message(e)}")

    # UNWATCH — stop watching a coin
    elif command == "unwatch" and len(parts) > 1:
        from core.watcher import stop_watcher
        symbol = parts[1].upper() + "USDT"
        if stop_watcher(symbol):
            notify(f"🛑 Stopped watching {parts[1].upper()}")
        else:
            notify(f"❌ Not watching {parts[1].upper()}")

    # WATCHING — list all active watchers
    elif command == "watching":
        from core.watcher import active_watchers
        if active_watchers:
            notify("👁 Active watchers:\n" + "\n".join(active_watchers.keys()))
        else:
            notify("No active watchers")

    # HELP
    elif command == "help":
        notify(
            """🤖 zTrading Bot Commands

🪙 TRADING:
• buy COIN 10 → buy $10 of COIN
• buy COIN 10 0.085 → with stop loss
• buy COIN 10 0.085 1.30 1.50 → stop + take profits
• buya COIN 10 → analyze first, buy if bullish
• sell COIN → force sell 100%
• sell COIN 50 → sell 50% of position
• setstop COIN 0.085 → update stop loss

🎯 ALERTS:
• alert COIN 1.70 10 1.60 → buy when price hits 1.70
• alerts → view all active alerts
• cancelalert COIN → cancel an alert

🤖 AUTO-TRADING:
• watch COIN 10 → auto-trade COIN with $10 (1D/4H/1H signal)
• watch COIN 10 0.085 → with stop loss
• watch COIN 10 0.085 1.30 1.50 → stop + take profits
• unwatch COIN → stop auto-trading
• watching → list active watchers

👀 TRACKING:
• track COIN → alert on 5% moves
• track COIN 3 → alert on 3% moves
• untrack COIN → stop tracking
• trackers → view tracked coins

📊 MONITORING:
• price COIN → current price
• status → active trades & P/L
• summary → daily summary
• balance → wallet balances
• orders COIN → last 5 orders
• analyze COIN → AI trend analysis
• history → last 10 closed trades
• stats → win rate and total P/L

⚙️ SETTINGS:
• set min_profit 1.5
• set trail_percent 5.0
• set hard_stop_loss -1.0
• set daily_loss_limit -10.0

❓ help → show this message"""
        )

    else:
        notify("❓ Unknown command! Send 'help' for available commands.")