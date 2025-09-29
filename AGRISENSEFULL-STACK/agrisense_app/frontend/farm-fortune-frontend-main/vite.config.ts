import { defineConfig } from "vite";
import react from "@vitejs/plugin-react-swc";
import path from "path";

// https://vitejs.dev/config/
export default defineConfig((ctx: { mode: string }) => ({
  // Ensure production build uses `/ui/` base path so assets resolve correctly
  base: ctx.mode === 'production' ? '/ui/' : '/',
  server: {
    host: "127.0.0.1",
    port: 3000,
    proxy: {
      // Proxy API calls in dev to FastAPI backend on 8004
      "/api": {
        target: process.env.VITE_API || "http://127.0.0.1:8004",
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/(api)(\/)?/, "/"),
      },
    },
  },
  plugins: [
    react(),
  ].filter(Boolean),
  resolve: {
    alias: {
      "@": path.resolve(path.dirname(new URL(import.meta.url).pathname), "./src"),
    },
  },
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ['react', 'react-dom'],
          ui: [
            '@radix-ui/react-accordion',
            '@radix-ui/react-alert-dialog',
            '@radix-ui/react-aspect-ratio',
            '@radix-ui/react-avatar',
            '@radix-ui/react-button',
            '@radix-ui/react-card',
            '@radix-ui/react-dialog',
            '@radix-ui/react-dropdown-menu',
            '@radix-ui/react-input',
            '@radix-ui/react-label',
            '@radix-ui/react-select',
            '@radix-ui/react-tabs',
            '@radix-ui/react-toast',
            '@radix-ui/react-tooltip'
          ],
          charts: ['recharts'],
          maps: ['leaflet', 'react-leaflet'],
          icons: ['lucide-react'],
          utils: ['clsx', 'tailwind-merge', 'class-variance-authority'],
          router: ['react-router-dom'],
          forms: ['react-hook-form', '@hookform/resolvers', 'zod'],
          query: ['@tanstack/react-query'],
          animation: ['framer-motion']
        }
      }
    },
    chunkSizeWarningLimit: 1000,
    sourcemap: ctx.mode === 'development',
    minify: ctx.mode === 'production' ? 'esbuild' : false,
    target: 'esnext'
  },
  optimizeDeps: {
    include: [
      'react', 
      'react-dom', 
      'lucide-react',
      '@tanstack/react-query',
      'framer-motion'
    ]
  },
  esbuild: {
    target: 'esnext',
    format: 'esm'
  }
}));
