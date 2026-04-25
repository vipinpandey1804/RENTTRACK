/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        brand: {
          50: "#eef4fb",
          100: "#d5e3f4",
          500: "#2e75b6",
          700: "#134074",
          900: "#0b2545",
        },
      },
    },
  },
  plugins: [],
};
