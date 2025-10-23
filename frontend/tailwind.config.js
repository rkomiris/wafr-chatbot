/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        wafr: {
          blue: "#1e3a8a",
          green: "#059669",
          slate: "#0f172a",
          sand: "#f8fafc",
        },
      },
    },
  },
  plugins: [],
}
