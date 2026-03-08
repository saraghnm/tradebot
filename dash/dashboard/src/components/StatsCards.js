"use client";

export default function StatsCards({ stats, tradeCount }) {
  const s = stats || {};

  const cards = [
    {
      label: "Total P/L",
      value: s.total_pnl != null ? `${s.total_pnl >= 0 ? "+" : ""}$${s.total_pnl?.toFixed(4)}` : "—",
      positive: s.total_pnl >= 0,
      sub: `${s.total_trades || 0} trades total`,
    },
    {
      label: "Win Rate",
      value: s.win_rate != null ? `${s.win_rate}%` : "—",
      positive: (s.win_rate || 0) >= 50,
      sub: `${s.wins || 0}W / ${s.losses || 0}L`,
    },
    {
      label: "Best Trade",
      value: s.best_trade != null ? `+$${s.best_trade?.toFixed(4)}` : "—",
      positive: true,
      sub: "All time",
    },
    {
      label: "Worst Trade",
      value: s.worst_trade != null ? `$${s.worst_trade?.toFixed(4)}` : "—",
      positive: false,
      sub: "All time",
    },
    {
      label: "Active Trades",
      value: tradeCount,
      positive: tradeCount > 0,
      sub: tradeCount === 1 ? "position open" : "positions open",
      neutral: true,
    },
    {
      label: "Avg Trade",
      value: s.avg_profit != null ? `${s.avg_profit >= 0 ? "+" : ""}$${s.avg_profit?.toFixed(4)}` : "—",
      positive: (s.avg_profit || 0) >= 0,
      sub: "Per closed trade",
    },
  ];

  return (
    <div className="grid grid-cols-2 md:grid-cols-3 xl:grid-cols-6 gap-3">
      {cards.map((card) => (
        <div
          key={card.label}
          className="rounded-lg p-4 border fade-in"
          style={{ background: "#111118", borderColor: "#1e1e2e" }}
        >
          <p className="text-xs mb-2" style={{ color: "#4a4a6a" }}>{card.label}</p>
          <p
            className={`text-lg font-semibold tabular-nums ${card.neutral ? "" : card.positive ? "glow-green" : "glow-red"}`}
            style={{
              color: card.neutral ? "#e2e2f0" : card.positive ? "#00ff88" : "#ff4466",
            }}
          >
            {card.value}
          </p>
          <p className="text-xs mt-1" style={{ color: "#2a2a4a" }}>{card.sub}</p>
        </div>
      ))}
    </div>
  );
}
