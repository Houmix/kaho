/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        brown: {
          50: '#F7F1EA',
          100: '#EBDCCB',
          200: '#D9C2A7',
          300: '#B8926F',
          500: '#8B5E3C',
          700: '#5C3D2E',
          800: '#4A3023',
          900: '#2B1D14',
        },
        cream: {
          50: '#FBF8F3',
          100: '#F5EFE6',
          200: '#EAE0D2',
          300: '#DCCFBC',
        },
        caramel: '#C8A97E',
      },
      fontFamily: {
        display: ['Fraunces', 'Georgia', 'serif'],
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
      boxShadow: {
        warm: '0 10px 30px -12px rgba(43, 29, 20, 0.25)',
      },
    },
  },
  plugins: [],
}
