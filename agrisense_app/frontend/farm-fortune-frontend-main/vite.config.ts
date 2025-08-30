import { defineConfig } from "vite";
import react from "@vitejs/plugin-react-swc";
import path from "path";

// https://vitejs.dev/config/
export default defineConfig((ctx: { mode: string }) => ({
  base: ctx.mode === 'production' ? '/ui/' : '/',
  server: {
    host: "::",
    port: 8080,
    proxy: {
      // Proxy API calls in dev to FastAPI backend on 8004
      "/api": {
        target: "http://127.0.0.1:8004",
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
}));
