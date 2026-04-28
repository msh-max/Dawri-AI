import type { Config } from 'tailwindcss';

const config: Config = {
  content: ['./src/**/*.{js,ts,jsx,tsx,mdx}'],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        // Saudi-inspired palette
        saudi: {
          50: '#e6f4ec',
          100: '#c2e4ce',
          200: '#9bd3af',
          300: '#6dbe8c',
          400: '#3ea968',
          500: '#1a8f4d',
          600: '#006c35', // Saudi flag green
          700: '#00582c',
          800: '#004523',
          900: '#00321a',
          950: '#001f10',
        },
        gold: {
          50: '#fbf7ec',
          100: '#f4eacb',
          200: '#ecd99e',
          300: '#dec370',
          400: '#d3b057',
          500: '#c9a14a', // primary gold
          600: '#a8843b',
          700: '#856630',
          800: '#5e4823',
          900: '#3a2c16',
        },
        ink: {
          50: '#f6f7f6',
          900: '#0f1715', // surface
          950: '#0a0e0c', // background
        },
      },
      fontFamily: {
        sans: ['var(--font-inter)', 'system-ui', 'sans-serif'],
        arabic: ['var(--font-plex-arabic)', 'system-ui', 'sans-serif'],
      },
      backgroundImage: {
        'radial-saudi':
          'radial-gradient(ellipse 80% 50% at 50% -20%, rgba(0,108,53,0.25), transparent 70%)',
        'gold-shine':
          'linear-gradient(135deg, #d3b057 0%, #c9a14a 40%, #856630 100%)',
      },
      boxShadow: {
        glow: '0 0 60px -10px rgba(0, 108, 53, 0.45)',
        'gold-glow': '0 0 40px -10px rgba(201, 161, 74, 0.55)',
      },
      animation: {
        'fade-up': 'fadeUp 0.6s ease-out forwards',
        shimmer: 'shimmer 2.4s linear infinite',
      },
      keyframes: {
        fadeUp: {
          '0%': { opacity: '0', transform: 'translateY(12px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        shimmer: {
          '0%': { backgroundPosition: '-200% 0' },
          '100%': { backgroundPosition: '200% 0' },
        },
      },
    },
  },
  plugins: [],
};

export default config;
