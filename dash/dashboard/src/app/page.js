"use client";

import { useState, useEffect, useCallback } from "react";
import StatsCards from "../components/StatsCards";
import ActiveTrades from "../components/ActiveTrades";
import EquityChart from "../components/EquityChart";
import TradeHistory from "../components/TradeHistory";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:5000";

export default function Dashboard() {
  const [state, setState] = useState(null);
  const [stats, setStats] = useState(null);
  const [equity, setEquity] = useState([]);
  const [history, setHistory] = useState([]);
  const [lastUpdated, setLastUpdated] = useState(null);
  const [online, setOnline] = useState(null);

  const fetchAll = useCallback(async () => {
    try {
      const [stateRes, statsRes, equityRes, historyRes] = await Promise.all([
        fetch(`${API}/api/state`),
        fetch(`${API}/api/stats`),
        fetch(`${API}/api/equity`),
        fetch(`${API}/api/history`),
      ]);
      const [stateData, statsData, equityData, historyData] = await Promise.all([
        stateRes.json(),
        statsRes.json(),
        equityRes.json(),
        historyRes.json(),
      ]);
      setState(stateData);
      setStats(statsData);
      setEquity(equityData);
      setHistory(historyData);
      setLastUpdated(new Date());
      setOnline(true);
    } catch {
      setOnline(false);
    }
  }, []);

  useEffect(() => {
    fetchAll();
    const interval = setInterval(fetchAll, 30000);
    return () => clearInterval(interval);
  }, [fetchAll]);

  const activeTrades = state?.active_trades || {};
  const dailyPnl = state?.daily_pnl || 0;
  const tradeCount = Object.keys(activeTrades).length;

  return (
    <div className="min-h-screen" style={{ background: "#0a0a0f" }}>
      {/* Header */}
      <header className="border-b border-border px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-4">
          <div>
            <h1 className="font-display text-xl font-bold tracking-tight" style={{ color: "#e2e2f0", fontFamily: "'Syne', sans-serif" }}>
              z<span style={{ color: "#00ff88" }}>Trading</span> Bot
            </h1>
            <p className="text-xs mt-0.5" style={{ color: "#4a4a6a" }}>Live Dashboard</p>
          </div>
        </div>

        <div className="flex items-center gap-6">
          <div className="text-right">
            <p className="text-xs" style={{ color: "#4a4a6a" }}>Daily P/L</p>
            <p className={`text-lg font-semibold ${dailyPnl >= 0 ? "glow-green" : "glow-red"}`}
               style={{ color: dailyPnl >= 0 ? "#00ff88" : "#ff4466" }}>
              {dailyPnl >= 0 ? "+" : ""}${dailyPnl.toFixed(4)}
            </p>
          </div>

          <div className="flex items-center gap-2">
            <span className={`w-2 h-2 rounded-full pulse-dot ${online ? "bg-green-400" : "bg-red-500"}`}
                  style={{ background: online ? "#00ff88" : "#ff4466" }} />
            <span className="text-xs" style={{ color: "#4a4a6a" }}>
              {online === null ? "connecting..." : online ? "live" : "offline"}
            </span>
          </div>

          {lastUpdated && (
            <span className="text-xs" style={{ color: "#2a2a4a" }}>
              {lastUpdated.toLocaleTimeString()}
            </span>
          )}
        </div>
      </header>

      <main className="p-6 space-y-6 max-w-7xl mx-auto">
        {/* Stats row */}
        <StatsCards stats={stats} tradeCount={tradeCount} />

        {/* Chart + Active Trades */}
        <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
          <div className="xl:col-span-2">
            <EquityChart equity={equity} />
          </div>
          <div>
            <ActiveTrades trades={activeTrades} />
          </div>
        </div>

        {/* History */}
        <TradeHistory history={history} />
      </main>
    </div>
  );
}
