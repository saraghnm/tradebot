# trader.py
from state import save_state, load_state
import time
from binance.client import Client
from config import API_KEY, API_SECRET, settings
from notifier import notify

client = Client(API_KEY, API_SECRET)
client.timestamp_offset = client.get_server_time()["serverTime"] - int(
    time.time() * 1000
)

# Load state from file on startup
_state = load_state()
active_trades = _state["active_trades"]
daily_pnl = _state["daily_pnl"]

def monitor_alert(symbol, target_price, usdt_amount, custom_stop_price=None):
    notify(f"🔔 Alert set!\n{symbol} will buy at ${target_price}\nAmount: ${usdt_amount}")
    
    while True:
        try:
            current_price = get_price(symbol)
            
            if current_price <= target_price:
                notify(f"🔔 Alert triggered!\n{symbol} hit ${current_price}\nBuying now...")
                quantity, entry_price = buy(symbol, usdt_amount)
                thread = threading.Thread(
                    target=monitor_trade,
                    args=(symbol, quantity, entry_price, usdt_amount, custom_stop_price)
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
        # Get actual balance instead of stored quantity
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

def monitor_trade(symbol, quantity, entry_price, investment, custom_stop_price=None):
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
        "custom_stop_price": custom_stop_price,
    }
    save_state(active_trades, daily_pnl)


    

    while True:
        try:
            current_price = get_price(symbol)
            current_value = quantity * current_price
            profit = current_value - investment

            # Custom price stop loss
            if custom_stop_price and current_price <= custom_stop_price:
                sell(symbol, quantity)
                daily_pnl += profit
                active_trades.pop(symbol, None)
                save_state(active_trades, daily_pnl)
                notify(f"🛑 Price stop-loss hit!\nSold {symbol} at ${current_price}\nLoss: ${profit:.4f}")
                break

            # Daily loss limit
            if daily_pnl + profit <= settings["daily_loss_limit"]:
                sell(symbol, quantity)
                daily_pnl += profit
                active_trades.pop(symbol, None)
                save_state(active_trades, daily_pnl)
                notify(f"🚫 Daily loss limit hit!\nTotal daily P/L: ${daily_pnl:.4f}")
                break

            # Hard stop loss
            if profit <= hard_stop_loss:
                sell(symbol, quantity)
                daily_pnl += profit
                active_trades.pop(symbol, None)
                save_state(active_trades, daily_pnl)
                notify(f"⛔ SELL - Hard stop-loss hit!\nLoss limited to: ${profit:.4f}")
                break

            # Update highest value
            if current_value > highest_value:
                highest_value = current_value
                if trailing_active:
                    stop_loss_value = highest_value - trail_amount

            # Activate trailing stop
            if not trailing_active and profit >= min_profit:
                trailing_active = True
                stop_loss_value = highest_value - trail_amount
                notify(f"📈 Trailing stop ACTIVATED\nStop-loss at: ${stop_loss_value:.4f}")

            # Check trailing stop
            if trailing_active and current_value <= stop_loss_value:
                sell(symbol, quantity)
                daily_pnl += profit
                active_trades.pop(symbol, None)
                save_state(active_trades, daily_pnl)
                notify(f"🔴 SELL - Trailing stop hit!\nFinal profit: ${profit:.4f}\nDaily P/L: ${daily_pnl:.4f}")
                break

        except Exception as e:
                notify(f"⚠️ Error in {symbol}: {e}")
                time.sleep(30)
                continue

        time.sleep(2)

def startup_check():
    try:
        client.get_account()
    except Exception as e:
        notify(f"❌ Binance connection failed!\n{e}")
        exit(1)