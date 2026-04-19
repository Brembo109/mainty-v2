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
        surface: {
          DEFAULT: "var(--color-surface)",
          card:     "var(--color-surface-card)",
          elevated: "var(--color-surface-elevated)",
        },
        border: {
          DEFAULT: "var(--color-border)",
          subtle: "var(--color-border-subtle)",
          strong: "var(--color-border-strong)",
        },
        content: {
          primary:   "var(--color-content-primary)",
          secondary: "var(--color-content-secondary)",
          tertiary:  "var(--color-content-tertiary)",
        },
        accent: {
          DEFAULT: "var(--color-accent)",
          fg:      "var(--color-accent-fg)",
          soft:    "var(--color-accent-soft)",
        },
        status: {
          success:      "var(--color-status-success)",
          warning:      "var(--color-status-warning)",
          danger:       "var(--color-status-danger)",
          "success-bg": "var(--color-status-success-bg)",
          "warning-bg": "var(--color-status-warning-bg)",
          "danger-bg":  "var(--color-status-danger-bg)",
        },
      },
      fontFamily: {
        sans: [
          "Geist",
          "-apple-system",
          "BlinkMacSystemFont",
          '"Segoe UI"',
          "system-ui",
          "sans-serif",
        ],
        mono: [
          '"Geist Mono"',
          "ui-monospace",
          "SFMono-Regular",
          "Menlo",
          "Consolas",
          '"Liberation Mono"',
          "monospace",
        ],
      },
      borderRadius: {
        DEFAULT: "6px",
        sm:  "4px",
        md:  "6px",
        lg:  "8px",
      },
      fontSize: {
        "2xs": ["0.625rem", { lineHeight: "1rem" }],
      },
      height: {
        7:  "1.75rem",  // 28px — nav-item, button
        9:  "2.25rem",  // 36px — table row
        12: "3rem",     // 48px — topbar
      },
    },
  },
  plugins: [],
};
