/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./dist/*.{html,js}"],
  theme: {
    extend: {
      colors: {
        'logogreen': '#0D442F',
      },
    },
  },
  plugins: [require("daisyui")],
}

