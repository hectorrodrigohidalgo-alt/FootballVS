import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import { defineConfig } from 'vitest/config'

// React aporta JSX y recarga rápida; Tailwind analiza las clases durante el build.
export default defineConfig({
  plugins: [react(), tailwindcss()],
  // jsdom simula el navegador para probar componentes sin abrir una ventana real.
  test: {
    clearMocks: true,
    environment: 'jsdom',
    // Un solo worker evita sobrecargar equipos modestos y runners gratuitos.
    maxWorkers: 1,
    pool: 'threads',
    restoreMocks: true,
    setupFiles: './src/test/setup.ts',
  },
})
