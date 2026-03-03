# core/analyzer.py

import anthropic
from core.trader import get_price, client
from config import ANTHROPIC_API_KEY


def get_candle_data(symbol, interval="1h", limit=24):
    klines = client.get_klines(symbol=symbol, interval=interval, limit=limit)
    candles = []
    for k in klines:
        candles.append(
            {
                "open": float(k[1]),
                "high": float(k[2]),
                "low": float(k[3]),
                "close": float(k[4]),
                "volume": float(k[5]),
            }
        )
    return candles


def analyze_coin(symbol):
    try:
        current_price = get_price(symbol)

        # Fetch 3 timeframes
        candles_1h = get_candle_data(symbol, interval="1h", limit=24)
        candles_4h = get_candle_data(symbol, interval="4h", limit=24)
        candles_1d = get_candle_data(symbol, interval="1d", limit=14)

        def summarize(candles):
            closes = [c["close"] for c in candles]
            highs = [c["high"] for c in candles]
            lows = [c["low"] for c in candles]
            volumes = [c["volume"] for c in candles]
            return {
                "closes": closes,
                "high": max(highs),
                "low": min(lows),
                "change": ((closes[-1] - closes[0]) / closes[0] * 100),
                "avg_volume": sum(volumes) / len(volumes),
                "last_volume": volumes[-1],
            }

        s1h = summarize(candles_1h)
        s4h = summarize(candles_4h)
        s1d = summarize(candles_1d)

        price_data = f"""
Symbol: {symbol}
Current Price: ${current_price}

1H Timeframe (last 24 candles):
  Closes: {s1h['closes']}
  High: ${s1h['high']} | Low: ${s1h['low']}
  Change: {s1h['change']:.2f}%
  Volume vs avg: {((s1h['last_volume'] / s1h['avg_volume']) * 100):.0f}%

4H Timeframe (last 24 candles):
  Closes: {s4h['closes']}
  High: ${s4h['high']} | Low: ${s4h['low']}
  Change: {s4h['change']:.2f}%
  Volume vs avg: {((s4h['last_volume'] / s4h['avg_volume']) * 100):.0f}%

1D Timeframe (last 14 candles):
  Closes: {s1d['closes']}
  High: ${s1d['high']} | Low: ${s1d['low']}
  Change: {s1d['change']:.2f}%
  Volume vs avg: {((s1d['last_volume'] / s1d['avg_volume']) * 100):.0f}%
"""

        ai_client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        message = ai_client.messages.create(
            model="claude-opus-4-6",
            max_tokens=600,
            messages=[
                {
                    "role": "user",
                    "content": f"""You are a crypto trading analyst. Analyze this multi-timeframe data and give a concise trading analysis.

{price_data}

Respond in this exact format:
1H Trend: [Bullish/Bearish/Sideways]
4H Trend: [Bullish/Bearish/Sideways]
1D Trend: [Bullish/Bearish/Sideways]
Overall: [Bullish/Bearish/Sideways]
Strength: [Strong/Moderate/Weak]
RSI estimate: [Overbought/Neutral/Oversold]
Support: $[price]
Resistance: $[price]
Re-entry safe: [Yes/No]
Suggested re-entry: $[price or 'Wait']
Summary: [2 sentences max]""",
                }
            ],
        )

        return message.content[0].text

    except Exception as e:
        error_str = str(e)
        if "529" in error_str or "overloaded" in error_str.lower():
            return "⏳ AI is overloaded right now, try again in a few minutes!"
        elif "Invalid symbol" in error_str:
            return "❌ Invalid coin symbol!"
        elif "authentication" in error_str.lower():
            return "❌ API key error, check your Anthropic key!"
        else:
            return f"❌ Analysis failed: {e}"
