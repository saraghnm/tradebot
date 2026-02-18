from binance.client import Client
import time

API_KEY = "aOTcjlBaQbkqixyGGkJ0J9HIfs1qSCeQH8YYsk2MOqqs26JxGe0S2XP4jJq93bZB"
API_SECRET = "dOrGyL4Ru65wSseKKOgHqJuHrlpMHBgzA03ke6SE31kbYQRKpJE31POGnPZOEYpH"


client = Client(API_KEY, API_SECRET, testnet=True)
client.timestamp_offset = client.get_server_time()['serverTime'] - int(time.time() * 1000)

def get_price(symbol):
    ticker = client.get_symbol_ticker(symbol=symbol)
    return float(ticker['price'])

def get_lot_size(symbol):
    info = client.get_symbol_info(symbol)
    for f in info['filters']:
        if f['filterType'] == 'LOT_SIZE':
            return float(f['stepSize'])
    return 0.000001

def buy(symbol, usdt_amount):
    price = get_price(symbol)
    step_size = get_lot_size(symbol)
    
    raw_quantity = usdt_amount / price
    # Round down to the nearest valid step size
    precision = len(str(step_size).rstrip('0').split('.')[-1])
    quantity = round(raw_quantity - (raw_quantity % step_size), precision)
    
    order = client.order_market_buy(symbol=symbol, quantity=quantity)
    print(f"✅ BUY order placed! Quantity: {quantity} at ~${price:,.2f}")
    return quantity, price

def sell(symbol, quantity):
    order = client.order_market_sell(symbol=symbol, quantity=quantity)
    print(f"✅ SELL order placed! Quantity: {quantity}")
    return order

# Settings
symbol = "DOGEUSDT"
investment = 10
min_profit = 1.0
trail_amount = 0.50
hard_stop_loss = -1.0

# Place real buy order
print("Placing BUY order on testnet...\n")
quantity, entry_price = buy(symbol, investment)

print(f"\nEntry price:   ${entry_price:,.2f}")
print(f"Quantity:      {quantity} BTC")
print(f"\nWaiting for ${min_profit} profit to activate trailing stop...\n")

highest_value = investment
stop_loss_value = None
trailing_active = False

while True:
    current_price = get_price(symbol)
    current_value = quantity * current_price
    profit = current_value - investment

    # 1. Hard stop-loss check (always first!)
    if profit <= hard_stop_loss:
        print(f"\n  ⛔ HARD STOP-LOSS HIT! Placing sell order...")
        sell(symbol, quantity)
        print(f"  Loss limited to: ${profit:.4f}")
        break

    # 2. Update highest value
    if current_value > highest_value:
        highest_value = current_value
        if trailing_active:
            stop_loss_value = highest_value - trail_amount
            print(f"  📈 New high! Stop-loss moved to ${stop_loss_value:.4f}")

    if not trailing_active and profit >= min_profit:
        trailing_active = True
        stop_loss_value = highest_value - trail_amount
        print(f"  🟢 Trailing stop ACTIVATED at value ${stop_loss_value:.4f}\n")

    if trailing_active and current_value <= stop_loss_value:
        print(f"\n  🔴 STOP-LOSS HIT! Placing sell order...")
        sell(symbol, quantity)
        print(f"  Final profit: ${profit:.4f}")
        break

    status = f"TRAILING (stop: ${stop_loss_value:.4f})" if trailing_active else "WAITING"
    print(f"Price: ${current_price:,.2f} | Value: ${current_value:.4f} | P/L: ${profit:.4f} | {status}")

    time.sleep(2)

print("\nTrade complete! ✅")