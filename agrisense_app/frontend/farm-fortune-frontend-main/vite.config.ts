import { defineConfig } from "vite";
import react from "@vitejs/plugin-react-swc";
import path from "path";

// https://vitejs.dev/config/
export default defineConfig((ctx: { mode: string }) => ({
  base: ctx.mode === 'production' ? '/ui/' : '/',
  server: {
    host: "::",
    port: 8080,
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
