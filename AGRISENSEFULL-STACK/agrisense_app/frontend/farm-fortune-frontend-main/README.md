# farm-fortune-frontend-main

## Development

Environment variables:

Create a `.env` file at project root if you want to point to a running backend in dev:

```dotenv
VITE_API_URL=http://127.0.0.1:8004
```

Run the dev server (default port 8080; Vite may switch if in use):

```bash
npm install
npm run dev
```

Build for production:

```bash
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

- During development, API calls are proxied from the Vite dev server to the backend on [http://127.0.0.1:8004](http://127.0.0.1:8004) via `/api` (works regardless of the dev port).
- In production, the UI is served by the backend under `/ui` and uses same-origin requests.
