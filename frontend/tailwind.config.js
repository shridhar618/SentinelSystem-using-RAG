/** @type {import('tailwindcss').Config} */
// Colours resolve to CSS variables (see src/index.css) so the whole app follows
// the ShareLock paper-and-sage theme in light mode and its ink theme in dark mode.
const v = (name) => `rgb(var(--${name}) / <alpha-value>)`
// Every shade of a Tailwind palette family resolves to one themed token.
const scale = (name) => Object.fromEntries(
  [50, 100, 200, 300, 400, 500, 600, 700, 800, 900, 950].map((k) => [k, v(name)]).concat([['DEFAULT', v(name)]])
)

export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter', 'ui-sans-serif', 'system-ui', 'sans-serif'],
        mono: ['IBM Plex Mono', 'JetBrains Mono', 'monospace'],
        display: ['Syne', 'Inter', 'sans-serif'],
      },
      colors: {
        // `white` is the foreground ink in both themes.
        white: v('ink'),
        bg: {
          900: v('bg-900'),
          800: v('bg-800'),
          700: v('bg-700'),
          600: v('bg-600'),
        },
        accent: {
          DEFAULT: v('accent'),
          dim: v('accent-dim'),
          glow: 'rgb(var(--accent) / 0.15)',
        },
        danger: v('danger'),
        warn: v('warn'),
        success: v('success'),
        purple: scale('purple'), violet: scale('purple'), fuchsia: scale('purple'),
        sky: scale('info'), blue: scale('info'), indigo: scale('info'),
        teal: scale('accent'),
        emerald: scale('success'), green: scale('success'), lime: scale('success'),
        amber: scale('warn'), yellow: scale('warn'), orange: scale('warn'),
        rose: scale('danger'), red: scale('danger'), pink: scale('danger'),
        slate: {
          100: v('tone-100'), 200: v('tone-200'), 300: v('tone-300'), 400: v('tone-400'),
          500: v('tone-500'), 600: v('tone-600'), 700: v('tone-700'), 800: v('bg-600'), 900: v('bg-700'),
        },
        gray: {
          100: v('tone-100'), 200: v('tone-200'), 300: v('tone-300'), 400: v('tone-400'),
          500: v('tone-500'), 600: v('tone-600'), 700: v('line'), 800: v('bg-700'), 900: v('bg-800'),
        },
        cyan: scale('accent'),
      },
      // Borders written as border-white/N become the sage line colour, scaled so
      // faint utility opacities (5-10%) still read as a visible hairline.
      // Used by the many /2../8 modifiers in the pages (e.g. border-white/8).
      opacity: { 2: '0.02', 3: '0.03', 4: '0.04', 6: '0.06', 7: '0.07', 8: '0.08', 12: '0.12', 15: '0.15', 35: '0.35', 45: '0.45' },
      borderColor: { DEFAULT: 'rgb(var(--line))', white: 'rgb(var(--line) / calc(<alpha-value> * 9))' },
      divideColor: { white: 'rgb(var(--line) / calc(<alpha-value> * 9))' },
      boxShadow: {
        glow: '0 8px 28px -12px rgb(var(--accent) / 0.45)',
        'glow-lg': '0 14px 40px -14px rgb(var(--accent) / 0.55)',
        card: '0 1px 0 rgb(var(--highlight) / 0.6) inset, 0 12px 32px -18px rgb(var(--shadow) / 0.45)',
      },
      animation: {
        'pulse-slow': 'pulse 3s ease-in-out infinite',
        'fade-in': 'fadeIn 0.4s ease forwards',
        'slide-up': 'slideUp 0.4s ease forwards',
        'slide-in': 'slideIn 0.3s ease forwards',
        typing: 'typing 1.2s ease-in-out infinite',
      },
      keyframes: {
        fadeIn: { from: { opacity: 0 }, to: { opacity: 1 } },
        slideUp: { from: { opacity: 0, transform: 'translateY(16px)' }, to: { opacity: 1, transform: 'translateY(0)' } },
        slideIn: { from: { opacity: 0, transform: 'translateX(-16px)' }, to: { opacity: 1, transform: 'translateX(0)' } },
        typing: {
          '0%, 100%': { opacity: 0.2 },
          '50%': { opacity: 1 },
        },
      },
    },
  },
  plugins: [],
}
