"""FastAPI backend wiring the chatbot to the new NLM pipeline."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Dict

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi import Request
from fastapi.responses import FileResponse, HTMLResponse

from agrisense_app.backend.chatbot_service import router as chat_router
from agrisense_app.backend.nlp.nlu_service import NLUService
from agrisense_app.backend.nlp.response_generator import ResponseGenerator
from fastapi import Response

app = FastAPI(title="AgriSense Backend", version="1.0.0")

_logger = logging.getLogger("agrisense.backend")
_nlu = NLUService()
_response_gen = ResponseGenerator()


@app.on_event("startup")
async def _startup() -> None:
    """Log startup to indicate NLM wiring is ready."""
    _logger.info("NLM chatbot pipeline initialised")


@app.get("/__routes", include_in_schema=False)
async def debug_routes():
    """Return a concise list of app routes for debugging order/registration."""
    routes = []
    for r in app.routes:
        methods = getattr(r, 'methods', None)
        routes.append({
            'path': getattr(r, 'path', str(r)),
            'name': getattr(r, 'name', None),
            'methods': sorted(list(methods)) if methods else None,
        })
    return routes


@app.get("/health")
async def health_check() -> Dict[str, str]:
    """Basic health endpoint."""
    return {"status": "ok"}


@app.post("/chatbot/ask")
async def chatbot_ask(payload: Dict[str, str]) -> JSONResponse:
    """Single endpoint that routes queries through NLM components."""

    question = (payload or {}).get("question")
    if not question:
        raise HTTPException(status_code=400, detail="question is required")

    intent, confidence = _nlu.recognize_intent(question)
    entities = _nlu.extract_entities(question)
    answer = _response_gen.generate(intent, entities)

    return JSONResponse({
        "question": question,
        "results": [
            {
                "rank": 1,
                "score": confidence,
                "answer": answer,
                "intent": intent,
                "entities": entities,
            }
        ],
    })


# Routers --------------------------------------------------------------
app.include_router(chat_router, prefix="/api")


# Static frontend ------------------------------------------------------
FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend" / "farm-fortune-frontend-main" / "dist"
if FRONTEND_DIR.exists():
    # Prefer mounting the assets subfolder to ensure our custom UI fallback
    # gets a chance to respond with index.html for client-side routes like
    # /ui/chatbot. StaticFiles at /ui would otherwise take precedence and
    # produce 404s for routes that are intended to be handled by the SPA.
    assets_dir = FRONTEND_DIR / "assets"
    if assets_dir.exists():
        app.mount("/ui/assets", StaticFiles(directory=str(assets_dir)), name="ui_assets")
    else:
        # Fall back to mounting the whole dist at /ui when assets are not in a
        # dedicated subdirectory (older builds). This preserves backward
        # compatibility.
        app.mount("/ui", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="ui")


# Specific SPA fallback for the UI mount: if an asset file exists, return it; otherwise
# return index.html so the client-side router can handle the path. This ensures
# routes like /ui/chatbot and /ui/soil-analysis load the SPA instead of producing 404s.
@app.get("/ui/{full_path:path}", include_in_schema=False)
async def ui_spa_fallback(full_path: str, request: Request):
    if request.method != "GET":
        raise HTTPException(status_code=405, detail="Method not allowed")

    # If the requested path maps to a real file in the dist, serve it directly
    asset_path = FRONTEND_DIR / full_path
    _logger.debug("ui_spa_fallback: requested=%s asset_path=%s", full_path, str(asset_path))
    if asset_path.exists() and asset_path.is_file():
        _logger.info("ui_spa_fallback: serving asset %s", str(asset_path))
        # Serve static assets with default FileResponse. Hashed assets are safe to cache.
        return FileResponse(asset_path)

    # Otherwise serve the SPA entrypoint so client-side routing can take over
    index_file = FRONTEND_DIR / "index.html"
    _logger.debug("ui_spa_fallback: index_file=%s exists=%s", str(index_file), index_file.exists())
    if index_file.exists():
        # Prevent aggressive caching of the SPA entrypoint during development so new
        # builds are picked up without needing to clear the browser cache.
        _logger.info("ui_spa_fallback: serving index.html for %s", full_path)
        return FileResponse(index_file, headers={"Cache-Control": "no-cache, no-store, must-revalidate"})

    # Dist missing: fall back to the same helpful HTML as the global handler
    hint_html = """
    <!doctype html>
    <html>
        <head><meta charset='utf-8'><title>UI not built</title></head>
        <body style='font-family:system-ui,Segoe UI,Roboto,Arial;background:#fafafa;color:#222;padding:2rem'>
            <h1>Frontend not found</h1>
            <p>The pre-built frontend assets are not present on the server.</p>
            <p>To build and serve the UI locally, run the frontend build and restart the server:</p>
            <pre style='background:#fff;border:1px solid #ddd;padding:0.5rem'>
cd agrisense_app/frontend/farm-fortune-frontend-main
npm install
npm run build
            </pre>
            <p>After building, refresh this page. API endpoints remain available at <a href="/health">/health</a> and under <code>/api</code>.</p>
        </body>
    </html>
    """
    return HTMLResponse(hint_html, status_code=200)


# SPA fallback: return index.html for unknown GET paths so client-side routing works.
# This must be after routers/static mounts so API and asset routes are matched first.
@app.get("/{full_path:path}", include_in_schema=False)
async def spa_fallback(full_path: str, request: Request):
    # Only handle GET navigation requests from browsers
    if request.method != "GET":
        raise HTTPException(status_code=405, detail="Method not allowed")

    # If the frontend is present, serve its index.html so the client router can take over
    if FRONTEND_DIR.exists():
        index_file = FRONTEND_DIR / "index.html"
        if index_file.exists():
            return FileResponse(index_file)

    # Frontend dist is missing — return a helpful HTML page so browser navigation doesn't show a JSON 404
    hint_html = """
    <!doctype html>
    <html>
        <head><meta charset='utf-8'><title>UI not built</title></head>
        <body style='font-family:system-ui,Segoe UI,Roboto,Arial;background:#fafafa;color:#222;padding:2rem'>
            <h1>Frontend not found</h1>
            <p>The pre-built frontend assets are not present on the server.</p>
            <p>To build and serve the UI locally, run the frontend build and restart the server:</p>
            <pre style='background:#fff;border:1px solid #ddd;padding:0.5rem'>
cd agrisense_app/frontend/farm-fortune-frontend-main
npm install
npm run build
            </pre>
            <p>After building, refresh this page. API endpoints remain available at <a href="/health">/health</a> and under <code>/api</code>.</p>
        </body>
    </html>
    """
    return HTMLResponse(hint_html, status_code=200)

