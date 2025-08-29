import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  base: '/ui/',
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/recommend': 'http://127.0.0.1:8004',
  '/suggest_crop': 'http://127.0.0.1:8004',
  '/plants': 'http://127.0.0.1:8004',
      '/ingest': 'http://127.0.0.1:8004',
      '/recent': 'http://127.0.0.1:8004',
      '/live': 'http://127.0.0.1:8004',
      '/ready': 'http://127.0.0.1:8004'
    }
  },
  build: {
    outDir: 'dist',
    emptyOutDir: true
  }
})
