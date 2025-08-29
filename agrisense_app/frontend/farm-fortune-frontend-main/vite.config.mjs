import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react-swc';
import path from 'path';
import { fileURLToPath } from 'url';

export default defineConfig(({ mode }) => ({
  base: mode === 'production' ? '/ui/' : '/',
  server: { host: '::', port: 8080 },
  plugins: [react()],
  resolve: {
    alias: {
  // Use fileURLToPath for correct Windows path handling
  '@': path.resolve(fileURLToPath(new URL('.', import.meta.url)), 'src'),
    },
  },
}));
