import type { Config } from 'tailwindcss';

const config: Config = {
  darkMode: ['class'],
  content: [
    './pages/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
    './app/**/*.{js,ts,jsx,tsx,mdx}',
    './src/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ['var(--font-inter)', 'system-ui', 'sans-serif'],
        display: ['var(--font-eb-garamond)', 'serif'],
      },
      backgroundImage: {
        'gradient-radial': 'radial-gradient(var(--tw-gradient-stops))',
        'gradient-conic':
          'conic-gradient(from 180deg at 50% 50%, var(--tw-gradient-stops))',
      },
      borderRadius: {
        lg: 'var(--radius)',
        md: 'calc(var(--radius) - 2px)',
        sm: 'calc(var(--radius) - 4px)',
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
        destructive: {
          DEFAULT: 'hsl(var(--destructive))',
          foreground: 'hsl(var(--destructive-foreground))',
        },
        border: 'hsl(var(--border))',
        input: 'hsl(var(--input))',
        ring: 'hsl(var(--ring))',
        chart: {
          '1': 'hsl(var(--chart-1))',
          '2': 'hsl(var(--chart-2))',
          '3': 'hsl(var(--chart-3))',
          '4': 'hsl(var(--chart-4))',
          '5': 'hsl(var(--chart-5))',
        },
        // SiteSync palette — direct hex utilities
        'dark-espresso': '#211715',
        cocoa: '#4A3028',
        mahogany: '#6E3B32',
        crimson: '#A8323E',
        'warm-ivory': '#F7F0E5',
        'soft-sand': '#E9DCCB',
        'muted-rose': '#C98F89',

        // brand scale: dark-espresso (900) → warm-ivory (50)
        brand: {
          50:  '#F7F0E5',   // warm ivory
          100: '#E9DCCB',   // soft sand
          200: '#C98F89',   // muted rose
          300: '#AA6259',
          400: '#8A4A41',
          500: '#A8323E',   // crimson
          600: '#8E2833',
          700: '#6E3B32',   // mahogany
          800: '#4A3028',   // cocoa
          900: '#211715',   // dark espresso
          950: '#140D0C',
        },
      },
      boxShadow: {
        brutal: '4px 4px 0px 0px var(--brutal-shadow)',
        'brutal-sm': '2px 2px 0px 0px var(--brutal-shadow)',
        'brutal-lg': '6px 6px 0px 0px var(--brutal-shadow)',
        'brutal-xl': '8px 8px 0px 0px var(--brutal-shadow)',
      },
      keyframes: {
        'accordion-down': {
          from: { height: '0' },
          to: { height: 'var(--radix-accordion-content-height)' },
        },
        'accordion-up': {
          from: { height: 'var(--radix-accordion-content-height)' },
          to: { height: '0' },
        },
        'bounce-dot': {
          '0%, 80%, 100%': { transform: 'scale(0)' },
          '40%': { transform: 'scale(1)' },
        },
      },
      animation: {
        'accordion-down': 'accordion-down 0.2s ease-out',
        'accordion-up': 'accordion-up 0.2s ease-out',
        'bounce-dot': 'bounce-dot 1.4s infinite ease-in-out both',
      },
    },
  },
  plugins: [require('tailwindcss-animate')],
};
export default config;
