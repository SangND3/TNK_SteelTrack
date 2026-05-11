/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./templates/**/*.html",
    "../backend/apps/**/templates/**/*.html",
    "./static_src/js/**/*.js",
  ],
  theme: {
    extend: {
      colors: {
        // ── TNK brand palette ────────────────────────────────────────────────
        tnk: {
          blue:        "#0056A8",   // Primary brand blue
          "blue-dark": "#003E7A",   // Hover / pressed state
          "blue-light":"#E8F2FC",   // Tinted bg
          orange:      "#F5821E",   // Diamond accent (top facet)
          "orange-dark":"#D66A0A",  // Hover
          silver:      "#B0B4BA",   // Diamond side facets
          "silver-light": "#E8EAEC",
        },
        // ── Industry steel palette ───────────────────────────────────────────
        steel: {
          50:  "#F0F4F8",
          100: "#D9E2EC",
          200: "#BCCCDC",
          300: "#9FB3C8",
          400: "#829AB1",
          500: "#627D98",
          600: "#486581",
          700: "#334E68",
          800: "#243B53",
          900: "#102A43",
        },
      },
      fontFamily: {
        sans: ["Inter", "ui-sans-serif", "system-ui", "sans-serif"],
      },
      backgroundImage: {
        "steel-pattern": "url(\"data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' fill-rule='evenodd'%3E%3Cg fill='%23ffffff' fill-opacity='0.04'%3E%3Cpath d='M36 34v-4h-2v4h-4v2h4v4h2v-4h4v-2h-4zm0-30V0h-2v4h-4v2h4v4h2V6h4V4h-4zM6 34v-4H4v4H0v2h4v4h2v-4h4v-2H6zM6 4V0H4v4H0v2h4v4h2V6h4V4H6z'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E\")",
      },
      keyframes: {
        "fade-in": {
          "0%": { opacity: "0", transform: "translateY(-8px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        "slide-in": {
          "0%": { opacity: "0", transform: "translateX(-12px)" },
          "100%": { opacity: "1", transform: "translateX(0)" },
        },
      },
      animation: {
        "fade-in": "fade-in 0.25s ease-out",
        "slide-in": "slide-in 0.2s ease-out",
      },
    },
  },
  plugins: [
    require("@tailwindcss/forms"),
    require("@tailwindcss/typography"),
  ],
};
