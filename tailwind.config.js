/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./dist/*.{html,js}"],
  theme: {
    extend: {
      colors: {
        'logogreen': '#0D442F',
        'logogreen2': '#E2FFF4'
      },
    },
  },
  plugins: [require("daisyui")],
}

