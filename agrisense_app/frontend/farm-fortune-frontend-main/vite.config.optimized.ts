import { defineConfig } from "vite";
import react from "@vitejs/plugin-react-swc";
import path from "path";
import { visualizer } from 'rollup-plugin-visualizer';
import viteCompression from 'vite-plugin-compression';

// Hardware-optimized Vite configuration
// Intel Core Ultra 9 275HX (32 threads) + RTX 5060 (8GB)
export default defineConfig((ctx: { mode: string }) => ({
  // Ensure production build uses `/ui/` base path
  base: ctx.mode === 'production' ? '/ui/' : '/',
  
  server: {
    host: "127.0.0.1",
    port: 3000,
    strictPort: false,
    // Faster HMR with optimized settings
    hmr: {
      overlay: true,
    },
    watch: {
      usePolling: false,  // Faster than polling
      interval: 100,
    },
    proxy: {
      "/api": {
        target: process.env.VITE_API_URL || "http://127.0.0.1:8004",
        changeOrigin: true,
        secure: false,
        ws: true,
        rewrite: (path) => path.replace(/^\/api/, ''),
        configure: (proxy, _options) => {
          proxy.on('error', (err, _req, _res) => {
            console.log('Proxy error:', err);
          });
          proxy.on('proxyReq', (proxyReq, req, _res) => {
            console.log('Proxying:', req.method, req.url, '->', proxyReq.path);
          });
        }
      },
      "/health": {
        target: process.env.VITE_API_URL || "http://127.0.0.1:8004",
        changeOrigin: true,
        secure: false,
      },
    },
  },
  
  plugins: [
    react(),
    
    // Gzip compression (production only)
    ctx.mode === 'production' && viteCompression({
      algorithm: 'gzip',
      ext: '.gz',
      threshold: 10240, // 10KB minimum
      deleteOriginFile: false,
    }),
    
    // Brotli compression (better than gzip, production only)
    ctx.mode === 'production' && viteCompression({
      algorithm: 'brotliCompress',
      ext: '.br',
      threshold: 10240,
      deleteOriginFile: false,
    }),
    
    // Bundle size analyzer (run with ANALYZE=true)
    process.env.ANALYZE && visualizer({
      filename: './dist/stats.html',
      open: true,
      gzipSize: true,
      brotliSize: true,
    }),
  ].filter(Boolean),
  
  resolve: {
    alias: {
      "@": path.resolve(path.dirname(new URL(import.meta.url).pathname), "./src"),
    },
  },
  
  // Optimize dependency pre-bundling
  optimizeDeps: {
    include: [
      'react',
      'react-dom',
      'react-router-dom',
      '@tanstack/react-query',
    ],
    esbuildOptions: {
      target: 'es2020',
      // Use all CPU threads for esbuild
      workers: true,
    },
  },
  
  build: {
    target: 'es2020',
    
    // Use Terser for better compression (slower but smaller)
    minify: 'terser',
    terserOptions: {
      compress: {
        drop_console: true,      // Remove console.log in production
        drop_debugger: true,      // Remove debugger statements
        passes: 3,                // Multiple optimization passes
        pure_funcs: ['console.log', 'console.info'],  // Remove these functions
      },
      mangle: {
        safari10: false,  // No need for old Safari
      },
      format: {
        comments: false,  // Remove all comments
      },
    },
    
    // Rollup options for code splitting
    rollupOptions: {
      output: {
        // Optimize chunk naming for better caching
        chunkFileNames: 'assets/[name]-[hash].js',
        entryFileNames: 'assets/[name]-[hash].js',
        assetFileNames: 'assets/[name]-[hash].[ext]',
        
        // Manual chunks for optimal loading
        manualChunks: (id) => {
          // Core vendor chunk (critical path - load first)
          if (id.includes('node_modules/react') || id.includes('node_modules/react-dom')) {
            return 'vendor-react';
          }
          
          // Router (critical)
          if (id.includes('react-router-dom')) {
            return 'vendor-router';
          }
          
          // Data fetching (critical for API calls)
          if (id.includes('@tanstack/react-query')) {
            return 'vendor-query';
          }
          
          // UI components (lazy load)
          if (id.includes('@radix-ui')) {
            return 'ui-components';
          }
          
          // Charts library (heavy, lazy load)
          if (id.includes('recharts') || id.includes('d3-')) {
            return 'lib-charts';
          }
          
          // Maps library (heavy, lazy load)
          if (id.includes('leaflet') || id.includes('react-leaflet')) {
            return 'lib-maps';
          }
          
          // Icons (separate for better caching)
          if (id.includes('lucide-react')) {
            return 'ui-icons';
          }
          
          // i18n translations (lazy load)
          if (id.includes('react-i18next') || id.includes('i18next')) {
            return 'lib-i18n';
          }
          
          // Utility libraries
          if (id.includes('clsx') || id.includes('tailwind-merge') || 
              id.includes('class-variance-authority') || id.includes('date-fns')) {
            return 'utils';
          }
          
          // Form handling
          if (id.includes('react-hook-form') || id.includes('@hookform') || 
              id.includes('zod')) {
            return 'lib-forms';
          }
          
          // Animation libraries
          if (id.includes('framer-motion')) {
            return 'lib-animation';
          }
          
          // All other node_modules
          if (id.includes('node_modules')) {
            return 'vendor-misc';
          }
        },
      },
      
      // Parallelize builds (use all 32 threads!)
      maxParallelFileOps: 32,
    },
    
    // Chunk size warning limit (1MB)
    chunkSizeWarningLimit: 1000,
    
    // Report compressed size (shows bundle efficiency)
    reportCompressedSize: true,
    
    // Disable sourcemaps in production for faster builds
    sourcemap: ctx.mode === 'development',
    
    // Enable CSS code splitting
    cssCodeSplit: true,
    
    // Inline assets < 10KB as base64
    assetsInlineLimit: 10240,
    
    // Output directory
    outDir: 'dist',
    emptyOutDir: true,
    
    // CommonJS options
    commonjsOptions: {
      transformMixedEsModules: true,
    },
  },
  
  // Preview server (for testing production builds)
  preview: {
    host: "127.0.0.1",
    port: 4173,
    strictPort: false,
  },
}));
