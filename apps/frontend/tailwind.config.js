/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      fontFamily: {
        display: ["Syne", "sans-serif"],
        sans: ["DM Sans", "sans-serif"],
      },
      colors: {
        teal:   "#0ec4a8",
        amber:  "#f5a623",
        coral:  "#f06060",
        indigo: "#6b7ff5",
        mint:   "#4ade80",
      },
    },
  },
  plugins: [],
};
