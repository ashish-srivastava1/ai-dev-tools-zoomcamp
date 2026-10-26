import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// In dev, /api and /health are proxied to the FastAPI backend on :8000, so the
// browser talks to one origin (same as in the container, where FastAPI serves the UI).
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': 'http://localhost:8000',
      '/health': 'http://localhost:8000',
    },
  },
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: ['./src/test/setup.js'],
    css: false,
  },
})
