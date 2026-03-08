/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      fontFamily: {
        mono: ["'IBM Plex Mono'", "monospace"],
        display: ["'Syne'", "sans-serif"],
      },
      colors: {
        bg: "#0a0a0f",
        surface: "#111118",
        border: "#1e1e2e",
        accent: "#00ff88",
        red: "#ff4466",
        muted: "#4a4a6a",
        text: "#e2e2f0",
        dim: "#8888aa",
      },
    },
  },
  plugins: [],
};
