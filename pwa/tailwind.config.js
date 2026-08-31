/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        display: ['EB Garamond', 'serif'],
      },
      borderColor: {
        border: 'hsl(var(--border))',
      },
      colors: {
        background: 'hsl(var(--background))',
        foreground: 'hsl(var(--foreground))',
        card: {
          DEFAULT: 'hsl(var(--card))',
          foreground: 'hsl(var(--card-foreground))',
        },
        popover: {
          DEFAULT: 'hsl(var(--popover))',
          foreground: 'hsl(var(--popover-foreground))',
        },
        primary: {
          DEFAULT: 'hsl(var(--primary))',
          foreground: 'hsl(var(--primary-foreground))',
        },
        secondary: {
          DEFAULT: 'hsl(var(--secondary))',
          foreground: 'hsl(var(--secondary-foreground))',
        },
        muted: {
          DEFAULT: 'hsl(var(--muted))',
          foreground: 'hsl(var(--muted-foreground))',
        },
        accent: {
          DEFAULT: 'hsl(var(--accent))',
          foreground: 'hsl(var(--accent-foreground))',
        },
        border: 'hsl(var(--border))',
        input: 'hsl(var(--input))',
        ring: 'hsl(var(--ring))',

        // SiteSync palette
        'dark-espresso': '#211715',
        cocoa: '#4A3028',
        mahogany: '#6E3B32',
        crimson: '#A8323E',
        'warm-ivory': '#F7F0E5',
        'soft-sand': '#E9DCCB',
        'muted-rose': '#C98F89',

        brand: {
          50:  '#F7F0E5',
          100: '#E9DCCB',
          200: '#C98F89',
          300: '#AA6259',
          400: '#8A4A41',
          500: '#A8323E',
          600: '#8E2833',
          700: '#6E3B32',
          800: '#4A3028',
          900: '#211715',
        },
      },
      boxShadow: {
        brutal: '4px 4px 0px 0px var(--brutal-shadow)',
        'brutal-sm': '2px 2px 0px 0px var(--brutal-shadow)',
        'brutal-lg': '6px 6px 0px 0px var(--brutal-shadow)',
        'brutal-xl': '8px 8px 0px 0px var(--brutal-shadow)',
      }
    },
  },
  plugins: [],
}
