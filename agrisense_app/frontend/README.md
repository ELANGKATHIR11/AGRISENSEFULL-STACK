# AgriSense Frontend (React + TypeScript + Tailwind)

This folder contains the React UI for AgriSense, built with Vite, TypeScript, and Tailwind CSS.

Dev server:
- Proxies API calls to the FastAPI backend at http://127.0.0.1:8004
- Start backend first (VS Code task runs on 127.0.0.1:8004)

Build and serve:
- `npm run build` creates `dist/`
- Backend automatically serves `frontend/dist` at `/ui` if present

Notes:
- Vite base path is `/ui/` so assets load correctly when served by FastAPI
- Tailwind/PostCSS configs use CommonJS (`*.cjs`) to work with ESM package.json