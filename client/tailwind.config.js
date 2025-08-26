/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx,ts,tsx}"],
  theme: {
    extend: {
      fontFamily: {
        sans: ["Poppins", "ui-sans-serif", "system-ui", "Segoe UI", "Roboto", "Arial", "Noto Sans", "Apple Color Emoji", "Segoe UI Emoji"],
      },
      colors: {
        brand: {
          50: "#ecfdf5",
          100: "#d1fae5",
          200: "#a7f3d0",
          300: "#6ee7b7",
          400: "#34d399",
          500: "#10b981",
          600: "#059669",
          700: "#047857",
          800: "#065f46",
          900: "#064e3b",
        },
      },
      boxShadow: {
        'soft': '0 10px 30px -10px rgba(0,0,0,0.6)',
        'glow': '0 0 0 1px rgba(16,185,129,0.35), 0 10px 30px -10px rgba(16,185,129,0.45)',
      },
      backgroundImage: {
        'radial-soft': 'radial-gradient(1200px 600px at 50% -10%, rgba(16,185,129,0.14), transparent 60%)',
        'linear-sheen': 'linear-gradient(135deg, rgba(16,185,129,0.22), rgba(6,182,212,0.18))',
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
