import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ember: "#fc5000",
        "plasma-violet": "#524ae9",
        sulfur: "#f5f28e",
        limestone: "#f7f6f2",
        pumice: "#e2e2df",
        obsidian: "#070607",
        chalk: "#ffffff",
      },
      fontFamily: {
        display: ["var(--font-display)", "ui-sans-serif", "system-ui", "sans-serif"],
        body: ["var(--font-body)", "ui-sans-serif", "system-ui", "sans-serif"],
        system: ["system-ui", "-apple-system", "sans-serif"],
      },
      fontSize: {
        caption: ["12px", { lineHeight: "1.2" }],
        "body-sm": ["14px", { lineHeight: "1.2" }],
        body: ["16px", { lineHeight: "1.55" }],
        subheading: ["26px", { lineHeight: "1.2" }],
        "heading-sm": ["30px", { lineHeight: "1.5" }],
        heading: ["32px", { lineHeight: "1", letterSpacing: "0.64px" }],
        "heading-lg": ["48px", { lineHeight: "1" }],
        "heading-2xl": ["80px", { lineHeight: "1.1" }],
        "heading-3xl": ["96px", { lineHeight: "0.95" }],
        display: ["189px", { lineHeight: "0.94" }],
      },
      spacing: {
        4: "4px",
        8: "8px",
        9: "9px",
        10: "10px",
        12: "12px",
        16: "16px",
        18: "18px",
        20: "20px",
        24: "24px",
        32: "32px",
        40: "40px",
        48: "48px",
        56: "56px",
        64: "64px",
        80: "80px",
        92: "92px",
      },
      borderRadius: {
        cards: "40px",
        pills: "800px",
        small: "16px",
        inputs: "100px",
        medium: "20px",
        buttons: "40px",
      },
      backgroundImage: {
        "hero-gradient": "linear-gradient(to top right, #524ae9, #fc5000)",
      },
    },
  },
  plugins: [],
};

export default config;
