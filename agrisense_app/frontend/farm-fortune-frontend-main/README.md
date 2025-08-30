# farm-fortune-frontend-main

## Development

Environment variables:

Create a `.env` file at project root if you want to point to a running backend in dev:

```
VITE_API_URL=http://127.0.0.1:8004
```

Run dev server on port 8080 (configured in `vite.config.ts`):

```
npm install
npm run dev
```

Build for production:

```
npm run build
```

The built files will be emitted to `dist/`; the FastAPI server serves `/ui` from that folder when present.

## Tech stack

- Vite
- TypeScript
- React
- shadcn-ui
- Tailwind CSS

## Notes

- During development, API calls are proxied from http://localhost:8080 to the backend on http://127.0.0.1:8004 via `/api`.
- In production, the UI is served by the backend under `/ui` and uses same-origin requests.
