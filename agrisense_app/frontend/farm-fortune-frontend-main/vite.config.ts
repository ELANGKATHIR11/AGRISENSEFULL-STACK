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
    strictPort: false, // Auto-increment port if 3000 is busy
    proxy: {
      // Proxy API calls in dev to FastAPI backend on 8004
      "/api": {
        target: process.env.VITE_API_URL || "http://127.0.0.1:8004",
        changeOrigin: true,
        secure: false,
        ws: true, // WebSocket support
        rewrite: (path) => path.replace(/^\/api/, ''), // Strip /api prefix before forwarding to backend
        configure: (proxy, _options) => {
          proxy.on('error', (err, _req, _res) => {
            console.log('Proxy error:', err);
          });
          proxy.on('proxyReq', (proxyReq, req, _res) => {
            console.log('Proxying:', req.method, req.url, '->', proxyReq.path);
          });
        }
      },
      // Health check endpoint
      "/health": {
        target: process.env.VITE_API_URL || "http://127.0.0.1:8004",
        changeOrigin: true,
        secure: false,
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
        manualChunks: (id) => {
          // Core vendor chunk (critical path)
          if (id.includes('node_modules/react') || id.includes('node_modules/react-dom')) {
            return 'vendor';
          }
          
          // UI components (lazy load)
          if (id.includes('@radix-ui')) {
            return 'ui';
          }
          
          // Charts library (heavy, separate chunk)
          if (id.includes('recharts')) {
            return 'charts';
          }
          
          // Maps library (heavy, separate chunk)
          if (id.includes('leaflet') || id.includes('react-leaflet')) {
            return 'maps';
          }
          
          // Icons (separate for better caching)
          if (id.includes('lucide-react')) {
            return 'icons';
          }
          
          // i18n translations (separate for lazy loading)
          if (id.includes('react-i18next') || id.includes('i18next')) {
            return 'i18n';
          }
          
          // Utility libraries
          if (id.includes('clsx') || id.includes('tailwind-merge') || id.includes('class-variance-authority')) {
            return 'utils';
          }
          
          // Router
          if (id.includes('react-router-dom')) {
            return 'router';
          }
          
          // Form handling
          if (id.includes('react-hook-form') || id.includes('@hookform') || id.includes('zod')) {
            return 'forms';
          }
          
          // Data fetching
          if (id.includes('@tanstack/react-query')) {
            return 'query';
          }
          
          // Animation
          if (id.includes('framer-motion')) {
            return 'animation';
          }
          
          // All other node_modules as common vendor chunk
          if (id.includes('node_modules')) {
            return 'vendor-common';
          }
        },
        // Asset file naming for better caching
        assetFileNames: (assetInfo) => {
          // Handle undefined name
          if (!assetInfo.name) {
            return `assets/[name]-[hash][extname]`;
          }
          
          const info = assetInfo.name.split('.');
          const ext = info[info.length - 1];
          if (/\.(png|jpe?g|svg|gif|webp|avif)$/.test(assetInfo.name)) {
            return `assets/images/[name]-[hash][extname]`;
          }
          if (/\.(woff|woff2|eot|ttf|otf)$/.test(assetInfo.name)) {
            return `assets/fonts/[name]-[hash][extname]`;
          }
          return `assets/[name]-[hash][extname]`;
        },
        chunkFileNames: 'js/[name]-[hash].js',
        entryFileNames: 'js/[name]-[hash].js',
      },
    },
    chunkSizeWarningLimit: 1000,
    sourcemap: ctx.mode === 'development',
    minify: ctx.mode === 'production' ? 'esbuild' : false,
    target: 'esnext',
    // Enable CSS code splitting
    cssCodeSplit: true,
    // Optimize asset inline limit (10kb)
    assetsInlineLimit: 10240,
    // Report compressed size
    reportCompressedSize: true,
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
