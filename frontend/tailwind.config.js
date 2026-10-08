/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        background: '#FAF9F6',
        surface: '#FFFFFF',
        primary: '#C15C3D',
        secondary: '#E8DED1',
        textMain: '#2C2A29',
        textMuted: '#6B6661',
        success: '#4A7C59',
        error: '#B23A48'
      },
      fontFamily: {
        sans: ['Inter', 'sans-serif'],
        serif: ['Merriweather', 'serif']
      }
    },
  },
  plugins: [],
}
