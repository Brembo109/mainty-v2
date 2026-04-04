/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./templates/**/*.html",
    "./apps/**/*.html",
    "./apps/**/*.py",
    "./mainty/**/*.py",
  ],
  theme: {
    extend: {
      colors: {
        // Vercel-dark palette
        surface: {
          DEFAULT: "#000000",
          card: "#111111",
          elevated: "#0a0a0a",
        },
        border: {
          DEFAULT: "#222222",
          subtle: "#1a1a1a",
          strong: "#333333",
        },
        content: {
          primary: "#ffffff",
          secondary: "#888888",
          tertiary: "#555555",
        },
        status: {
          success: "#00c853",
          warning: "#ffd600",
          danger: "#ff1744",
          "success-bg": "rgba(0, 200, 83, 0.1)",
          "warning-bg": "rgba(255, 214, 0, 0.1)",
          "danger-bg": "rgba(255, 23, 68, 0.1)",
        },
      },
      fontFamily: {
        sans: [
          "Inter",
          "ui-sans-serif",
          "system-ui",
          "-apple-system",
          "BlinkMacSystemFont",
          '"Segoe UI"',
          "sans-serif",
        ],
        mono: [
          "ui-monospace",
          "SFMono-Regular",
          '"SF Mono"',
          "Menlo",
          "Consolas",
          '"Liberation Mono"',
          "monospace",
        ],
      },
      borderRadius: {
        DEFAULT: "6px",
        sm: "4px",
        md: "6px",
        lg: "8px",
      },
      fontSize: {
        "2xs": ["0.625rem", { lineHeight: "1rem" }],
      },
    },
  },
  plugins: [],
};
