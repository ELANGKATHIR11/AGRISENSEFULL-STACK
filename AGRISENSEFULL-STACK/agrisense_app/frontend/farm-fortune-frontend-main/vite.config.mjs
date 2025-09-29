import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react-swc';
import path from 'path';
import { fileURLToPath } from 'url';

export default defineConfig(({ mode }) => ({
  base: mode === 'production' ? '/ui/' : '/',
  server: {
    // bind to IPv4 localhost for consistent localhost access on Windows
    host: '127.0.0.1',
    port: 8080,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8004',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/(api)(\/)?/, '/'),
      },
    },
  },
  plugins: [react()],
  resolve: {
    alias: {
      // Use fileURLToPath for correct Windows path handling
      '@': path.resolve(fileURLToPath(new URL('.', import.meta.url)), 'src'),
    },
  },
}));
