/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'navy-900': '#0a192f',
        'navy-800': '#112240',
        'navy-700': '#233554',
        'gold-500': '#fbbf24',
        'gold-400': '#fcd34d',
        'sky-500': '#00f2fe',
        'sky-600': '#4facfe'
      },
      fontFamily: {
        orbitron: ['Orbitron', 'sans-serif'],
        outfit: ['Outfit', 'sans-serif'],
      }
    },
  },
  plugins: [],
}
