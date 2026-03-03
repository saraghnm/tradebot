# core/analyzer.py

import anthropic
from core.trader import get_price, client
from config import ANTHROPIC_API_KEY


def get_candle_data(symbol, interval="1h", limit=24):
    klines = client.get_klines(symbol=symbol, interval=interval, limit=limit)
    candles = []
    for k in klines:
        candles.append({
            "time": k[0],
            "open": float(k[1]),
            "high": float(k[2]),
            "low": float(k[3]),
            "close": float(k[4]),
            "volume": float(k[5]),
        })
    return candles

def analyze_coin(symbol):
    try:
        candles = get_candle_data(symbol)
        current_price = get_price(symbol)
        
        # Build price summary for Claude
        closes = [c["close"] for c in candles]
        highs = [c["high"] for c in candles]
        lows = [c["low"] for c in candles]
        volumes = [c["volume"] for c in candles]
        
        price_data = f"""
Symbol: {symbol}
Current Price: ${current_price}
Last 24h closes: {closes}
Last 24h highs: {highs}
Last 24h lows: {lows}
Last 24h volumes: {volumes}
24h High: ${max(highs)}
24h Low: ${min(lows)}
Price change: {((closes[-1] - closes[0]) / closes[0] * 100):.2f}%
"""
        
        ai_client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        message = ai_client.messages.create(
            model="claude-opus-4-6",
            max_tokens=500,
            messages=[
                {
                    "role": "user",
                    "content": f"""You are a crypto trading analyst. Analyze this coin data and give a concise trading analysis.

{price_data}

Respond in this exact format:
Trend: [Bullish/Bearish/Sideways]
Strength: [Strong/Moderate/Weak]
RSI estimate: [Overbought/Neutral/Oversold]
Support: $[price]
Resistance: $[price]
Re-entry safe: [Yes/No]
Suggested re-entry: $[price or 'Wait']
Summary: [2 sentences max]"""
                }
            ],
        )
        
        return message.content[0].text
        
    except Exception as e:
        return f"Analysis failed: {e}"