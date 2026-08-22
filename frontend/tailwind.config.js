/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./app/**/*.{js,ts,jsx,tsx}", "./components/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        gaia: {
          green: "#2e7d32",
          light: "#4caf50",
          dark: "#1b5e20",
          bg: "#f4faf5",
        },
      },
    },
  },
  plugins: [],
}
