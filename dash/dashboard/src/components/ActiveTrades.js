"use client";

export default function ActiveTrades({ trades }) {
  const entries = Object.entries(trades);

  return (
    <div className="rounded-lg border p-5 fade-in h-full" style={{ background: "#111118", borderColor: "#1e1e2e" }}>
      <div className="flex items-center justify-between mb-4">
        <p className="text-sm font-semibold" style={{ color: "#e2e2f0", fontFamily: "'Syne', sans-serif" }}>
          Active Trades
        </p>
        <span
          className="text-xs px-2 py-0.5 rounded"
          style={{ background: "#1e1e2e", color: "#4a4a6a" }}
        >
          {entries.length} open
        </span>
      </div>

      {entries.length === 0 ? (
        <div className="flex items-center justify-center h-32">
          <p className="text-sm" style={{ color: "#2a2a4a" }}>No active positions</p>
        </div>
      ) : (
        <div className="space-y-3">
          {entries.map(([symbol, trade]) => {
            const pair = symbol.replace("USDT", "");
            const profit = trade.profit_estimate ?? null;
            const hasTP = trade.take_profit1 || trade.take_profit2;

            return (
              <div
                key={symbol}
                className="rounded p-3 border"
                style={{ background: "#0a0a0f", borderColor: "#1e1e2e" }}
              >
                <div className="flex items-center justify-between mb-2">
                  <span className="font-semibold text-sm" style={{ color: "#e2e2f0" }}>{pair}</span>
                  <span className="text-xs px-1.5 py-0.5 rounded"
                        style={{ background: "#1e1e2e", color: "#00ff88" }}>
                    LONG
                  </span>
                </div>

                <div className="grid grid-cols-2 gap-1 text-xs">
                  <span style={{ color: "#4a4a6a" }}>Entry</span>
                  <span className="text-right tabular-nums" style={{ color: "#e2e2f0" }}>
                    ${trade.entry_price?.toFixed(4)}
                  </span>

                  <span style={{ color: "#4a4a6a" }}>Invested</span>
                  <span className="text-right tabular-nums" style={{ color: "#e2e2f0" }}>
                    ${trade.investment?.toFixed(2)}
                  </span>

                  {trade.custom_stop_price && (
                    <>
                      <span style={{ color: "#4a4a6a" }}>Stop</span>
                      <span className="text-right tabular-nums" style={{ color: "#ff4466" }}>
                        ${trade.custom_stop_price?.toFixed(4)}
                      </span>
                    </>
                  )}

                  {trade.take_profit1 && (
                    <>
                      <span style={{ color: "#4a4a6a" }}>TP1</span>
                      <span className="text-right tabular-nums" style={{ color: "#00ff88" }}>
                        ${trade.take_profit1?.toFixed(4)}
                      </span>
                    </>
                  )}

                  {trade.take_profit2 && (
                    <>
                      <span style={{ color: "#4a4a6a" }}>TP2</span>
                      <span className="text-right tabular-nums" style={{ color: "#00ff88" }}>
                        ${trade.take_profit2?.toFixed(4)}
                      </span>
                    </>
                  )}

                  {trade.half_sold && (
                    <>
                      <span style={{ color: "#4a4a6a" }}>Status</span>
                      <span className="text-right" style={{ color: "#00ff88" }}>TP1 hit ✓</span>
                    </>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
