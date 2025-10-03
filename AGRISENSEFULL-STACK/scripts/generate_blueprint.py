#!/usr/bin/env python
"""Generate or update AGRISENSE_BLUEPRINT.md dynamic sections.

Idempotent: safe to run repeatedly. Falls back gracefully if imports fail.
"""
from __future__ import annotations
import os
import re
import sys
import json
import importlib
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any

ROOT = Path(__file__).resolve().parent.parent
BLUEPRINT = ROOT / "AGRISENSE_BLUEPRINT.md"
BACKEND_DIR = ROOT / "agrisense_app" / "backend"
REQ_FILE = BACKEND_DIR / "requirements.txt"
DATASETS_DIR = ROOT / "datasets"
MODELS_DIR = BACKEND_DIR

AUTO_BLOCKS = {
    "API": ("<!-- AUTO:API_START -->", "<!-- AUTO:API_END -->"),
    "ENV": ("<!-- AUTO:ENV_START -->", "<!-- AUTO:ENV_END -->"),
    "MODELS": ("<!-- AUTO:MODELS_START -->", "<!-- AUTO:MODELS_END -->"),
    "CHANGELOG": ("<!-- AUTO:CHANGELOG_START -->", "<!-- AUTO:CHANGELOG_END -->"),
}


def safe_import_app():
    sys.path.append(str(ROOT))
    try:
        os.environ.setdefault("AGRISENSE_DISABLE_ML", "1")  # speed
        from agrisense_app.backend.main import app  # type: ignore
        return app
    except Exception as e:
        return f"IMPORT_ERROR: {e}"


def extract_routes(app_or_err) -> List[Dict[str, Any]]:
    routes = []
    if isinstance(app_or_err, str):
        return []
    for r in getattr(app_or_err, "routes", []):
        methods = ",".join(sorted(set(getattr(r, "methods", [])) - {"HEAD", "OPTIONS"})) if hasattr(r, "methods") else ""
        path = getattr(r, "path", "?")
        name = getattr(r, "name", "")
        summary = getattr(getattr(r, "endpoint", None), "__doc__", "") or ""  # simple
        summary_short = summary.strip().splitlines()[0][:120] if summary else ""
        routes.append({"path": path, "methods": methods, "name": name, "summary": summary_short})
    routes.sort(key=lambda x: (x["path"], x["methods"]))
    return routes


ENV_VAR_PATTERN = re.compile(r'os\.getenv\(["\']([A-Z0-9_]+)["\']')

def scan_env_vars() -> List[str]:
    found = set()
    for py in BACKEND_DIR.rglob("*.py"):
        try:
            text = py.read_text(errors="ignore")
        except Exception:
            continue
        for m in ENV_VAR_PATTERN.finditer(text):
            found.add(m.group(1))
    return sorted(found)


def list_models() -> List[Dict[str, Any]]:
    exts = {".keras", ".joblib", ".pt", ".pth", ".onnx", ".npz"}
    models = []
    for f in MODELS_DIR.iterdir():
        if f.is_file() and f.suffix in exts:
            models.append({
                "name": f.name,
                "size_kb": round(f.stat().st_size / 1024, 1),
            })
    return sorted(models, key=lambda x: x["name"])


def dataset_catalog() -> Dict[str, Any]:
    catalog = {}
    if DATASETS_DIR.exists():
        for sub in DATASETS_DIR.iterdir():
            if sub.is_dir():
                catalog[sub.name] = len(list(sub.rglob("*")))
    return catalog


def parse_requirements() -> List[str]:
    if not REQ_FILE.exists():
        return []
    lines = []
    for line in REQ_FILE.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        lines.append(line)
    return lines


def make_api_table(routes: List[Dict[str, Any]]) -> str:
    if not routes:
        return "_No routes discovered (import failure or empty app)._"
    out = ["| Method(s) | Path | Name | Summary |", "|-----------|------|------|---------|"]
    for r in routes:
        out.append(f"| {r['methods']} | {r['path']} | {r['name']} | {r['summary']} |")
    return "\n".join(out)


def make_env_table(vars_: List[str]) -> str:
    if not vars_:
        return "_No environment variables discovered._"
    out = ["| Variable | Present |", "|----------|---------|"]
    for v in vars_:
        out.append(f"| {v} | yes |")
    return "\n".join(out)


def make_models_table(models: List[Dict[str, Any]]) -> str:
    if not models:
        return "_No model artifacts found in backend directory._"
    out = ["| Artifact | Size (KB) |", "|----------|-----------|"]
    for m in models:
        out.append(f"| {m['name']} | {m['size_kb']} |")
    return "\n".join(out)


def make_changelog_entry() -> str:
    ts = datetime.utcnow().isoformat(timespec="seconds") + "Z"
    return f"- Auto-update: {ts}"


def inject_block(content: str, block_key: str, payload: str) -> str:
    start, end = AUTO_BLOCKS[block_key]
    if start not in content:
        # Append block if missing
        return content + f"\n\n{start}\n{payload}\n{end}\n"
    pattern = re.compile(re.escape(start) + r".*?" + re.escape(end), re.DOTALL)
    return pattern.sub(f"{start}\n{payload}\n{end}", content)


def main():
    if not BLUEPRINT.exists():
        print(f"Blueprint file missing: {BLUEPRINT}")
        sys.exit(1)

    text = BLUEPRINT.read_text(encoding="utf-8")

    app_or_err = safe_import_app()
    routes = extract_routes(app_or_err)
    env_vars = scan_env_vars()
    models = list_models()

    api_section = make_api_table(routes)
    env_section = make_env_table(env_vars)
    models_section = make_models_table(models)
    changelog_line = make_changelog_entry()

    text = inject_block(text, "API", api_section)
    text = inject_block(text, "ENV", env_section)
    text = inject_block(text, "MODELS", models_section)

    # Append or extend changelog list
    start, end = AUTO_BLOCKS["CHANGELOG"]
    if start in text:
        # Insert new line at top of existing block body
        pattern = re.compile(re.escape(start) + r"(.*?)" + re.escape(end), re.DOTALL)
        m = pattern.search(text)
        if m:
            inner = m.group(1).strip()
            updated = f"{start}\n{changelog_line}\n" + (inner + "\n" if inner else "") + f"{end}"
            text = pattern.sub(updated, text)
    else:
        text += f"\n\n{start}\n{changelog_line}\n{end}\n"

    # Update last generated marker
    text = re.sub(r"Last generated:.*", f"Last generated: {datetime.utcnow().isoformat(timespec='seconds')}Z", text)

    BLUEPRINT.write_text(text, encoding="utf-8")
    print("✅ Blueprint updated successfully.")
    if isinstance(app_or_err, str):
        print(f"⚠️ App import issue (non-fatal): {app_or_err}")

if __name__ == "__main__":
    main()
