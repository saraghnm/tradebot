"use client";

import { useEffect, useRef } from "react";
import {
  Chart,
  LineElement,
  PointElement,
  LinearScale,
  CategoryScale,
  Filler,
  Tooltip,
} from "chart.js";

Chart.register(LineElement, PointElement, LinearScale, CategoryScale, Filler, Tooltip);

export default function EquityChart({ equity }) {
  const canvasRef = useRef(null);
  const chartRef = useRef(null);

  useEffect(() => {
    if (!canvasRef.current) return;

    const labels = equity.map((e) => {
      const d = new Date(e.timestamp);
      return `${d.getMonth() + 1}/${d.getDate()} ${d.getHours()}:${String(d.getMinutes()).padStart(2, "0")}`;
    });
    const data = equity.map((e) => e.cumulative);

    const isPositive = data.length === 0 || data[data.length - 1] >= 0;
    const lineColor = isPositive ? "#00ff88" : "#ff4466";

    if (chartRef.current) {
      chartRef.current.destroy();
    }

    const ctx = canvasRef.current.getContext("2d");
    const gradient = ctx.createLinearGradient(0, 0, 0, 300);
    gradient.addColorStop(0, isPositive ? "rgba(0,255,136,0.2)" : "rgba(255,68,102,0.2)");
    gradient.addColorStop(1, "rgba(0,0,0,0)");

    chartRef.current = new Chart(ctx, {
      type: "line",
      data: {
        labels: labels.length ? labels : ["—"],
        datasets: [
          {
            data: data.length ? data : [0],
            borderColor: lineColor,
            borderWidth: 2,
            backgroundColor: gradient,
            fill: true,
            tension: 0.4,
            pointRadius: data.length > 20 ? 0 : 3,
            pointBackgroundColor: lineColor,
            pointBorderColor: lineColor,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
          tooltip: {
            backgroundColor: "#111118",
            borderColor: "#1e1e2e",
            borderWidth: 1,
            titleColor: "#4a4a6a",
            bodyColor: "#e2e2f0",
            callbacks: {
              label: (ctx) => ` $${ctx.raw.toFixed(4)}`,
            },
          },
        },
        scales: {
          x: {
            grid: { color: "#1e1e2e", drawBorder: false },
            ticks: {
              color: "#2a2a4a",
              font: { family: "'IBM Plex Mono'", size: 10 },
              maxTicksLimit: 8,
            },
          },
          y: {
            grid: { color: "#1e1e2e", drawBorder: false },
            ticks: {
              color: "#2a2a4a",
              font: { family: "'IBM Plex Mono'", size: 10 },
              callback: (v) => `$${v.toFixed(2)}`,
            },
          },
        },
      },
    });

    return () => chartRef.current?.destroy();
  }, [equity]);

  return (
    <div className="rounded-lg border p-5 fade-in" style={{ background: "#111118", borderColor: "#1e1e2e" }}>
      <div className="flex items-center justify-between mb-4">
        <p className="text-sm font-semibold" style={{ color: "#e2e2f0", fontFamily: "'Syne', sans-serif" }}>
          Equity Curve
        </p>
        <p className="text-xs" style={{ color: "#4a4a6a" }}>{equity.length} trades</p>
      </div>
      <div style={{ height: "240px" }}>
        {equity.length === 0 ? (
          <div className="h-full flex items-center justify-center">
            <p className="text-sm" style={{ color: "#2a2a4a" }}>No trade history yet</p>
          </div>
        ) : (
          <canvas ref={canvasRef} />
        )}
      </div>
    </div>
  );
}
