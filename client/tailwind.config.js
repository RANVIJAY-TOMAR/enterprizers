/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx,ts,tsx}"],
  theme: {
    extend: {
      fontFamily: {
        sans: ["Inter", "ui-sans-serif", "system-ui", "Segoe UI", "Roboto", "Arial", "Noto Sans", "Apple Color Emoji", "Segoe UI Emoji"],
      },
      colors: {
        brand: {
          50: "#eef2ff",
          100: "#e0e7ff",
          200: "#c7d2fe",
          300: "#a5b4fc",
          400: "#818cf8",
          500: "#6366f1",
          600: "#4f46e5",
          700: "#4338ca",
          800: "#3730a3",
          900: "#312e81",
        },
      },
      boxShadow: {
        'soft': '0 10px 30px -10px rgba(0,0,0,0.6)',
        'glow': '0 0 0 1px rgba(99,102,241,0.35), 0 10px 30px -10px rgba(99,102,241,0.45)',
      },
      backgroundImage: {
        'radial-soft': 'radial-gradient(1200px 600px at 50% -10%, rgba(99,102,241,0.12), transparent 60%)',
        'linear-sheen': 'linear-gradient(135deg, rgba(99,102,241,0.2), rgba(56,189,248,0.15))',
      },
      borderRadius: {
        'xl2': '1.25rem',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0', transform: 'translateY(6px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        shimmer: {
          '0%': { backgroundPosition: '-100% 0' },
          '100%': { backgroundPosition: '200% 0' },
        },
        scaleIn: {
          '0%': { opacity: '0', transform: 'scale(0.98)' },
          '100%': { opacity: '1', transform: 'scale(1)' },
        },
      },
      animation: {
        'fade-in': 'fadeIn .5s ease-out both',
        'fade-in-slow': 'fadeIn .8s ease-out both',
        'scale-in': 'scaleIn .35s ease-out both',
        'shimmer': 'shimmer 2.5s linear infinite',
      },
    }
  },
  plugins: [],
};
