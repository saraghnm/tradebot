# trader.py

import time
from binance.client import Client
from config import API_KEY, API_SECRET, settings
from logger import log
from notifier import notify

client = Client(API_KEY, API_SECRET)
client.timestamp_offset = client.get_server_time()["serverTime"] - int(
    time.time() * 1000
)

# Track active trades
active_trades = {}
daily_pnl = 0.0


def get_price(symbol):
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
    log(f"✅ BUY order placed! Quantity: {quantity} at ~${price:,.4f}", type="trade")
    notify(f"🟢 BUY order placed!\nQuantity: {quantity} {symbol}\nPrice: ${price:,.4f}")
    return quantity, price


def sell(symbol, quantity):
    client.order_market_sell(symbol=symbol, quantity=quantity)
    log(f"✅ SELL order placed! Quantity: {quantity}", type="trade")


def monitor_trade(symbol, quantity, entry_price, investment):
    global daily_pnl
    min_profit = settings["min_profit"]
    trail_amount = settings["trail_amount"]
    hard_stop_loss = settings["hard_stop_loss"]
    highest_value = investment
    stop_loss_value = None
    trailing_active = False

    active_trades[symbol] = {
        "quantity": quantity,
        "entry_price": entry_price,
        "investment": investment,
    }

    log(f"👀 Monitoring {symbol}...", type="monitor")

    while True:
        try:
            current_price = get_price(symbol)
            current_value = quantity * current_price
            profit = current_value - investment

            if daily_pnl + profit <= settings["daily_loss_limit"]:
                log("🚫 DAILY LOSS LIMIT HIT!", type="trade")
                sell(symbol, quantity)
                daily_pnl += profit
                notify(f"🚫 Daily loss limit hit!\nStopped trading for today\nTotal daily P/L: ${daily_pnl:.4f}")
                break

            if profit <= hard_stop_loss:
                log("⛔ HARD STOP-LOSS HIT!", type="trade")
                sell(symbol, quantity)
                daily_pnl += profit
                notify(f"⛔ SELL - Hard stop-loss hit!\nLoss limited to: ${profit:.4f}")
                break

            if current_value > highest_value:
                highest_value = current_value
                if trailing_active:
                    stop_loss_value = highest_value - trail_amount
                    log(f"📈 New high! Stop-loss moved to ${stop_loss_value:.4f}", type="trade")

            if not trailing_active and profit >= min_profit:
                trailing_active = True
                stop_loss_value = highest_value - trail_amount
                log(f"🟢 Trailing stop ACTIVATED at ${stop_loss_value:.4f}", type="trade")
                notify(f"📈 Trailing stop ACTIVATED\nStop-loss at: ${stop_loss_value:.4f}")

            if trailing_active and current_value <= stop_loss_value:
                log("🔴 STOP-LOSS HIT!", type="trade")
                sell(symbol, quantity)
                daily_pnl += profit
                notify(f"🔴 SELL - Trailing stop hit!\nFinal profit: ${profit:.4f}\nDaily P/L: ${daily_pnl:.4f}")
                break

            status = (
                f"TRAILING (stop: ${stop_loss_value:.4f})"
                if trailing_active
                else "WAITING"
            )
            log(f"Price: ${current_price:,.4f} | Value: ${current_value:.4f} | P/L: ${profit:.4f} | {status}", type="monitor")

        except Exception as e:
            log(f"⚠️ Error: {e} — retrying in 5 seconds...", type="error")
            time.sleep(5)
            continue

        time.sleep(2)

    active_trades.pop(symbol, None)
    log("Trade complete! ✅")


def startup_check():
    try:
        client.get_account()
        log("✅ Binance connection OK", type="monitor")
    except Exception as e:
        log(f"❌ Binance connection failed: {e}", type="error")
        notify(f"❌ Binance connection failed!\n{e}")
        exit(1)