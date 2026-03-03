# trader.py
from core.state import save_state, load_state
import time
import threading
from binance.client import Client
from config import API_KEY, API_SECRET, settings
from core.notifier import notify
from core.stream import get_cached_price, start_stream

client = Client(API_KEY, API_SECRET)
client.timestamp_offset = client.get_server_time()["serverTime"] - int(
    time.time() * 1000
)

# Load state from file on startup
_state = load_state()
active_trades = _state["active_trades"]
daily_pnl = _state["daily_pnl"]
active_alerts = _state.get("active_alerts", {})
active_trackers = {}


def monitor_alert(symbol, target_price, usdt_amount, custom_stop_price=None):
    active_alerts[symbol] = {
        "target_price": target_price,
        "amount": usdt_amount,
        "custom_stop_price": custom_stop_price,
    }
    save_state(active_trades, daily_pnl, active_alerts)
    notify(f"🔔 Alert set!\n{symbol} will buy at ${target_price}\nAmount: ${usdt_amount}")

    while True:
        if symbol not in active_alerts:
            notify(f"🚫 Alert cancelled for {symbol}")
            break
        try:
            current_price = get_price(symbol)
            if current_price <= target_price:
                notify(f"🔔 Alert triggered!\n{symbol} hit ${current_price}\nBuying now...")
                active_alerts.pop(symbol, None)
                save_state(active_trades, daily_pnl, active_alerts)
                quantity, entry_price = buy(symbol, usdt_amount)
                thread = threading.Thread(
                    target=monitor_trade,
                    args=(symbol, quantity, entry_price, usdt_amount, custom_stop_price),
                )
                thread.daemon = True
                thread.start()
                break
        except Exception as e:
            notify(f"⚠️ Alert error {symbol}: {e}")
            time.sleep(30)
            continue
        time.sleep(5)


def get_price(symbol):
    cached = get_cached_price(symbol)
    if cached:
        return cached
    ticker = client.get_symbol_ticker(symbol=symbol)
    return float(ticker["price"])


def get_lot_size(symbol):
    info = client.get_symbol_info(symbol)
    for f in info["filters"]:
        if f["filterType"] == "LOT_SIZE":
            return float(f["stepSize"])
    return 0.000001


def buy(symbol, usdt_amount):
    price = get_price(symbol)
    step_size = get_lot_size(symbol)
    raw_quantity = usdt_amount / price
    precision = len(str(step_size).rstrip("0").split(".")[-1])
    quantity = round(raw_quantity - (raw_quantity % step_size), precision)
    client.order_market_buy(symbol=symbol, quantity=quantity)
    notify(f"🟢 BUY order placed!\nQuantity: {quantity} {symbol}\nPrice: ${price:,.4f}")
    return quantity, price


def sell(symbol, quantity):
    try:
        asset = symbol.replace("USDT", "")
        account = client.get_account()
        actual_balance = next(
            (float(a["free"]) for a in account["balances"] if a["asset"] == asset), 0
        )
        if actual_balance > 0:
            step_size = get_lot_size(symbol)
            precision = len(str(step_size).rstrip("0").split(".")[-1])
            quantity = round(actual_balance - (actual_balance % step_size), precision)
            client.order_market_sell(symbol=symbol, quantity=quantity)
            notify(f"✅ SELL order placed! Quantity: {quantity}")
        else:
            notify(f"⚠️ No balance to sell for {symbol}")
    except Exception as e:
        notify(f"❌ Sell error: {e}")

def monitor_tracker(symbol, alert_percent=5.0):
    last_price = get_price(symbol)
    notify(f"👀 Tracking {symbol} at ${last_price}\nWill alert on {alert_percent}% moves")
    
    while symbol in active_trackers:
        try:
            current_price = get_price(symbol)
            change = ((current_price - last_price) / last_price) * 100
            
            if abs(change) >= alert_percent:
                direction = "📈" if change > 0 else "📉"
                notify(f"{direction} {symbol} moved {change:.2f}%!\nFrom ${last_price} → ${current_price}")
                last_price = current_price

        except Exception as e:
            pass

        time.sleep(60)  # check every minute
    
    notify(f"🛑 Stopped tracking {symbol}")


def monitor_trade(symbol, quantity, entry_price, investment, custom_stop_price=None, take_profit1=None, take_profit2=None):
    global daily_pnl
    min_profit = settings["min_profit"]
    hard_stop_loss = settings["hard_stop_loss"]
    highest_price = entry_price
    stop_loss_price = None
    trailing_active = False
    half_sold = False
    original_quantity = quantity

    active_trades[symbol] = {
        "quantity": quantity,
        "entry_price": entry_price,
        "investment": investment,
        "custom_stop_price": custom_stop_price,
        "take_profit1": take_profit1,
        "take_profit2": take_profit2,
    }
    save_state(active_trades, daily_pnl, active_alerts)

    error_count = 0

    while True:
        try:
            current_price = get_price(symbol)
            current_value = quantity * current_price
            profit = current_value - investment

            # Reset error count on success
            if error_count > 0:
                error_count = 0
                notify(f"✅ Connection restored! Resuming {symbol}")

            # Custom price stop loss
            if custom_stop_price and current_price <= custom_stop_price:
                sell(symbol, quantity)
                daily_pnl += profit
                active_trades.pop(symbol, None)
                save_state(active_trades, daily_pnl, active_alerts)
                save_trade(symbol, entry_price, current_price, investment, profit, "Custom stop loss")
                notify(f"🛑 Price stop-loss hit!\nSold {symbol} at ${current_price}\nP/L: ${profit:.4f}")
                break

            # Daily loss limit
            if profit <= hard_stop_loss:
                sell(symbol, quantity)
                daily_pnl += profit
                active_trades.pop(symbol, None)
                save_state(active_trades, daily_pnl, active_alerts)
                save_trade(symbol, entry_price, current_price, investment, profit, "Hard stop loss")
                notify(f"⛔ SELL - Hard stop-loss hit!\nLoss limited to: ${profit:.4f}")
                break

            # Hard stop loss
            if profit <= hard_stop_loss:
                sell(symbol, quantity)
                daily_pnl += profit
                active_trades.pop(symbol, None)
                save_state(active_trades, daily_pnl, active_alerts)
                save_trade(symbol, entry_price, current_price, investment, profit, "Hard stop loss")
                notify(f"⛔ SELL - Hard stop-loss hit!\nLoss limited to: ${profit:.4f}")
                break

            # Take profit 1 — sell 50%
            if take_profit1 and not half_sold and current_price >= take_profit1:
                half_quantity = quantity / 2
                step_size = get_lot_size(symbol)
                precision = len(str(step_size).rstrip("0").split(".")[-1])
                half_quantity = round(half_quantity - (half_quantity % step_size), precision)
                client.order_market_sell(symbol=symbol, quantity=half_quantity)
                quantity = quantity - half_quantity
                half_sold = True
                half_profit = (take_profit1 - entry_price) * half_quantity
                notify(f"🎯 Take profit 1 hit!\nSold 50% of {symbol} at ${current_price}\nProfit locked: ${half_profit:.4f}\nHolding remaining: {quantity}")

            # Take profit 2 — activate trailing on rest
            if take_profit2 and half_sold and not trailing_active and current_price >= take_profit2:
                trailing_active = True
                highest_price = current_price
                stop_loss_price = highest_price * (1 - settings["trail_percent"] / 100)
                notify(f"🎯 Take profit 2 hit!\nTrailing stop ACTIVATED on remaining {symbol}\nStop-loss at: ${stop_loss_price:.4f}")

            # Update highest price
            if current_price > highest_price:
                highest_price = current_price
                if trailing_active:
                    stop_loss_price = highest_price * (1 - settings["trail_percent"] / 100)

            # Activate trailing stop (if no take profit levels set)
            if not trailing_active and not take_profit2 and profit >= min_profit:
                trailing_active = True
                stop_loss_price = highest_price * (1 - settings["trail_percent"] / 100)
                notify(f"📈 Trailing stop ACTIVATED\nStop-loss at: ${stop_loss_price:.4f}")

            # Check trailing stop
            if trailing_active and current_price <= stop_loss_price:
                sell(symbol, quantity)
                daily_pnl += profit
                active_trades.pop(symbol, None)
                save_state(active_trades, daily_pnl, active_alerts)
                save_trade(symbol, entry_price, current_price, investment, profit, "Trailing stop loss")
                notify(f"🔴 SELL - Trailing stop hit!\nFinal profit: ${profit:.4f}\nDaily P/L: ${daily_pnl:.4f}")
                
                # Auto re-entry analysis
                try:
                    from core.analyzer import analyze_coin
                    notify(f"🤖 Analyzing {symbol} for re-entry...")
                    analysis = analyze_coin(symbol)
                    
                    # Check if re-entry is safe
                    if "Re-entry safe: Yes" in analysis:
                        re_entry_price = round(current_price * 0.97, 6)  # 3% below sell
                        active_alerts[symbol] = {
                            "target_price": re_entry_price,
                            "amount": investment,
                            "custom_stop_price": custom_stop_price,
                        }
                        save_state(active_trades, daily_pnl, active_alerts)
                        thread = threading.Thread(
                            target=monitor_alert,
                            args=(symbol, re_entry_price, investment, custom_stop_price)
                        )
                        thread.daemon = True
                        thread.start()
                        notify(f"📌 Auto re-entry alert set!\n{symbol} → buy at ${re_entry_price}\n{analysis}")
                    else:
                        notify(f"⚠️ Re-entry not safe for {symbol}\n{analysis}")
                except Exception as e:
                    notify(f"⚠️ Auto re-entry analysis failed: {e}")
                
                break

        except Exception as e:
            error_count += 1

            if error_count == 3:
                notify(f"⚠️ Connection lost for {symbol}! Retrying...")

            if error_count < 3:
                time.sleep(5)
            elif error_count < 10:
                time.sleep(15)
            else:
                time.sleep(30)

            continue

        time.sleep(0.5)


def startup_check():
    try:
        client.get_account()
    except Exception as e:
        notify(f"❌ Binance connection failed!\n{e}")
        exit(1)