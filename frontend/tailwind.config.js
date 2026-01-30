const defaultTheme = require('tailwindcss/defaultTheme')

/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './src/**/*.{js,jsx,ts,tsx}',
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter', ...defaultTheme.fontFamily.sans],
        display: ['Space Grotesk', ...defaultTheme.fontFamily.sans],
      },
      colors: {
        // Custom industrial palette extensions if needed
        industrial: {
          50: '#F9FAFB',
          100: '#F3F4F6',
          900: '#111827',
        }
      }
    }
  },
  plugins: [],
};
