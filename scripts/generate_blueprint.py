"""Generate AUTO sections for AGRISENSE_BLUEPRINT.md.

This script introspects the FastAPI app in `agrisense_app.backend.main`, enumerates routes,
collects present environment variables, and lists model artifact files under
`agrisense_app/backend/`. It updates the AUTO:API, AUTO:ENV and AUTO:MODELS sections
in the blueprint file in-place.

Run from repo root (it will attempt to adjust sys.path):
  python scripts/generate_blueprint.py
"""

from __future__ import annotations
import os
import sys
import importlib
from pathlib import Path
from typing import List

# Try to locate the repository root that contains AGRISENSE_BLUEPRINT.md by walking up parents.
_p = Path(__file__).resolve()
BP_PATH = None
for i in range(1, 5):
    candidate = _p.parents[i]
    candidate_bp = candidate / "AGRISENSE_BLUEPRINT.md"
    if candidate_bp.exists():
        BP_PATH = candidate_bp
        REPO_ROOT = candidate
        break
if BP_PATH is None:
    # Fallback: assume repo root is two levels up (the AGRISENSEFULL-STACK folder)
    REPO_ROOT = Path(__file__).resolve().parents[1]
    BP_PATH = REPO_ROOT / "AGRISENSE_BLUEPRINT.md"

if not BP_PATH.exists():
    print(
        f"ERROR: Could not find AGRISENSE_BLUEPRINT.md at expected locations. Searched near {Path(__file__).resolve().parents[1]}"
    )
    sys.exit(2)
BACKEND_PKG = "agrisense_app.backend.main"


def safe_import_app():
    # Ensure repo root on sys.path so package imports work
    if str(REPO_ROOT) not in sys.path:
        sys.path.insert(0, str(REPO_ROOT))
    try:
        mod = importlib.import_module(BACKEND_PKG)
        app = getattr(mod, "app", None)
        return app
    except Exception:
        return None


def gen_api_table(app) -> str:
    if app is None:
        return "(Unable to import FastAPI app; ensure the app is importable)"
    rows: List[str] = []
    rows.append("| Method(s) | Path | Name | Summary |")
    rows.append("|-----------|------|------|---------|")
    for r in sorted(app.routes, key=lambda x: getattr(x, "path", "")):
        try:
            methods = ",".join(sorted(getattr(r, "methods", []) or []))
            path = getattr(r, "path", getattr(r, "path_format", ""))
            name = (
                getattr(r, "name", "") or getattr(r, "endpoint", lambda: None).__name__
            )
            summary = (
                (r.endpoint.__doc__ or "").splitlines()[0]
                if getattr(r, "endpoint", None) is not None
                else ""
            )
            rows.append(f"| {methods} | {path} | {name} | {summary} |")
        except Exception:
            continue
    return "\n".join(rows)


def gen_env_table() -> str:
    # Provide a practical list: environment variables currently set in process
    keys = sorted(os.environ.keys())
    rows = ["| Variable | Present |", "|----------|---------|"]
    for k in keys:
        rows.append(f"| {k} | yes |")
    return "\n".join(rows)


def gen_models_table() -> str:
    backend_dir = REPO_ROOT / "agrisense_app" / "backend"
    patterns = ["*.joblib", "*.keras", "*.h5", "*.npz", "*.pb", "*.model", "*.json"]
    items = []
    for pat in patterns:
        for p in sorted(backend_dir.glob(pat)):
            size_kb = round(p.stat().st_size / 1024.0, 1)
            items.append((p.name, size_kb))
    if not items:
        return "(No model artifacts found)"
    rows = ["| Artifact | Size (KB) |", "|----------|-----------|"]
    for name, size in items:
        rows.append(f"| {name} | {size} |")
    return "\n".join(rows)


def replace_section(
    text: str, start_marker: str, end_marker: str, new_body: str
) -> str:
    start = text.find(start_marker)
    end = text.find(end_marker, start)
    if start == -1 or end == -1:
        return text
    before = text[: start + len(start_marker)]
    after = text[end:]
    # Ensure new body is wrapped with newlines
    body = "\n" + new_body.strip() + "\n"
    return before + "\n" + body + after
def main():
    bp_path = BP_PATH  # type: ignore[var-annotated]
    if bp_path is None:
        print("ERROR: Could not find AGRISENSE_BLUEPRINT.md; BP_PATH is not set")
        sys.exit(2)
    text = bp_path.read_text(encoding="utf-8")
    app = safe_import_app()
    api_table = gen_api_table(app)
    env_table = gen_env_table()
    models_table = gen_models_table()

    text = replace_section(
        text, "<!-- AUTO:API_START -->", "<!-- AUTO:API_END -->", api_table
    )
    text = replace_section(
        text, "<!-- AUTO:ENV_START -->", "<!-- AUTO:ENV_END -->", env_table
    )
    text = replace_section(
        text, "<!-- AUTO:MODELS_START -->", "<!-- AUTO:MODELS_END -->", models_table
    )

    bp_path.write_text(text, encoding="utf-8")
    print("Blueprint updated:", bp_path)


if __name__ == "__main__":
    main()
if __name__ == "__main__":
    main()
