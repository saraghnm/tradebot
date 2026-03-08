# api.py
# Flask API server — exposes bot data for the web dashboard
# Run alongside bot.py: python api.py
# Endpoints: /api/state, /api/history, /api/stats, /api/health

from flask import Flask, jsonify
from flask_cors import CORS
import json
import os

app = Flask(__name__)
CORS(app)  # Allow requests from Next.js dashboard

STATE_FILE = "../state.json"
HISTORY_FILE = "../history.json"


def read_json(filepath):
    if os.path.exists(filepath):
        with open(filepath, "r") as f:
            return json.load(f)
    return None


@app.route("/api/health")
def health():
    return jsonify({"status": "ok"})


@app.route("/api/state")
def get_state():
    state = read_json(STATE_FILE)
    if state is None:
        return jsonify({"active_trades": {}, "daily_pnl": 0.0})
    return jsonify(state)


@app.route("/api/history")
def get_history():
    history = read_json(HISTORY_FILE)
    if history is None:
        return jsonify([])
    # Sort by timestamp descending, return last 50
    trades = sorted(history, key=lambda x: x.get("timestamp", ""), reverse=True)
    return jsonify(trades[:50])


@app.route("/api/stats")
def get_stats():
    history = read_json(HISTORY_FILE)
    if not history:
        return jsonify({
            "total_trades": 0,
            "wins": 0,
            "losses": 0,
            "win_rate": 0,
            "total_pnl": 0.0,
            "best_trade": 0.0,
            "worst_trade": 0.0,
            "avg_profit": 0.0,
        })

    profits = [t.get("profit", 0) for t in history]
    wins = [p for p in profits if p > 0]
    losses = [p for p in profits if p <= 0]

    return jsonify({
        "total_trades": len(history),
        "wins": len(wins),
        "losses": len(losses),
        "win_rate": round(len(wins) / len(history) * 100, 1) if history else 0,
        "total_pnl": round(sum(profits), 4),
        "best_trade": round(max(profits), 4) if profits else 0,
        "worst_trade": round(min(profits), 4) if profits else 0,
        "avg_profit": round(sum(profits) / len(profits), 4) if profits else 0,
    })


@app.route("/api/equity")
def get_equity():
    """Returns cumulative P/L over time for the equity curve chart."""
    history = read_json(HISTORY_FILE)
    if not history:
        return jsonify([])

    sorted_trades = sorted(history, key=lambda x: x.get("timestamp", ""))
    cumulative = 0.0
    equity_curve = []
    for trade in sorted_trades:
        cumulative += trade.get("profit", 0)
        equity_curve.append({
            "timestamp": trade.get("timestamp", ""),
            "symbol": trade.get("symbol", ""),
            "profit": round(trade.get("profit", 0), 4),
            "cumulative": round(cumulative, 4),
        })
    return jsonify(equity_curve)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
