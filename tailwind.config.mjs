/** @type {import('tailwindcss').Config} */
const config = {
  content: [
    "./app/**/*.{js,jsx,ts,tsx}",
    "./components/**/*.{js,jsx,ts,tsx}"
  ],
  theme: {
    extend: {
      colors: {
        'azul-control': '#1E3A8A',
        'verde-ahorro': '#16A34A',
        'gris-fondo': '#F5F7FA',
        'gris-texto': '#334155',
        'gris-secundario': '#94A3B8',
        'ambar-alerta': '#F59E0B',
        'rojo-error': '#DC2626',
      },
    },
  },
  plugins: [],
};

export default config;
