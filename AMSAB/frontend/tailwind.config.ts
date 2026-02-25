import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./src/**/*.{js,ts,jsx,tsx,mdx}"],
  theme: {
    extend: {
      colors: {
        bg: "#0d1117",
        surface: "#161b22",
        border: "#30363d",
        accent: "#58a6ff",
        success: "#3fb950",
        warning: "#d29922",
        danger: "#f85149",
        muted: "#8b949e",
      },
      animation: {
        pulse_slow: "pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite",
        flow: "flow 1.5s linear infinite",
      },
      keyframes: {
        flow: {
          "0%": { strokeDashoffset: "100" },
          "100%": { strokeDashoffset: "0" },
        },
      },
    },
  },
  plugins: [],
};

export default config;
