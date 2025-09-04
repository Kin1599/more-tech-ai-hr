/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Geologica', 'system-ui', 'sans-serif'],
        heading: ['Geologica', 'serif'],
        body: ['Geologica', 'sans-serif'],
        cursive: ['Geologica Cursive', 'cursive'],
        geologica: ['Geologica', 'sans-serif'],
      },
    },
  },
  plugins: [],
};
