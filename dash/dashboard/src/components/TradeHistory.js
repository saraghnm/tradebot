"use client";

import { useState } from "react";

export default function TradeHistory({ history }) {
  const [filter, setFilter] = useState("all");

  const filtered = history.filter((t) => {
    if (filter === "wins") return t.profit > 0;
    if (filter === "losses") return t.profit <= 0;
    return true;
  });

  return (
    <div className="rounded-lg border p-5 fade-in" style={{ background: "#111118", borderColor: "#1e1e2e" }}>
      <div className="flex items-center justify-between mb-4">
        <p className="text-sm font-semibold" style={{ color: "#e2e2f0", fontFamily: "'Syne', sans-serif" }}>
          Trade History
        </p>
        <div className="flex gap-1">
          {["all", "wins", "losses"].map((f) => (
            <button
              key={f}
              onClick={() => setFilter(f)}
              className="text-xs px-3 py-1 rounded capitalize transition-colors"
              style={{
                background: filter === f ? "#1e1e2e" : "transparent",
                color: filter === f ? "#e2e2f0" : "#4a4a6a",
                border: "1px solid",
                borderColor: filter === f ? "#2e2e4e" : "transparent",
              }}
            >
              {f}
            </button>
          ))}
        </div>
      </div>

      {filtered.length === 0 ? (
        <p className="text-sm text-center py-8" style={{ color: "#2a2a4a" }}>No trades yet</p>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-xs">
            <thead>
              <tr style={{ borderBottom: "1px solid #1e1e2e" }}>
                {["Symbol", "Entry", "Exit", "Invested", "Profit", "Reason", "Date"].map((h) => (
                  <th key={h} className="pb-2 text-left font-normal" style={{ color: "#4a4a6a" }}>
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {filtered.map((trade, i) => {
                const profit = trade.profit || 0;
                const date = trade.timestamp
                  ? new Date(trade.timestamp).toLocaleString("en-GB", {
                      day: "2-digit", month: "2-digit",
                      hour: "2-digit", minute: "2-digit",
                    })
                  : "—";

                return (
                  <tr
                    key={i}
                    style={{ borderBottom: "1px solid #0f0f1a" }}
                    className="hover:bg-opacity-50 transition-colors"
                  >
                    <td className="py-2.5 font-semibold" style={{ color: "#e2e2f0" }}>
                      {(trade.symbol || "").replace("USDT", "")}
                    </td>
                    <td className="py-2.5 tabular-nums" style={{ color: "#8888aa" }}>
                      ${trade.entry_price?.toFixed(4) ?? "—"}
                    </td>
                    <td className="py-2.5 tabular-nums" style={{ color: "#8888aa" }}>
                      ${trade.exit_price?.toFixed(4) ?? "—"}
                    </td>
                    <td className="py-2.5 tabular-nums" style={{ color: "#8888aa" }}>
                      ${trade.investment?.toFixed(2) ?? "—"}
                    </td>
                    <td
                      className="py-2.5 tabular-nums font-semibold"
                      style={{ color: profit >= 0 ? "#00ff88" : "#ff4466" }}
                    >
                      {profit >= 0 ? "+" : ""}${profit.toFixed(4)}
                    </td>
                    <td className="py-2.5" style={{ color: "#4a4a6a" }}>
                      {trade.reason || "—"}
                    </td>
                    <td className="py-2.5" style={{ color: "#2a2a4a" }}>
                      {date}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
