"""Simple PPTX analyzer utility.

This script extracts a short summary (titles, bullets, counts) from each slide.
It is intentionally small and dependency-safe: if python-pptx is missing, a clear
error is returned.
"""

import sys
import json
from pathlib import Path
from typing import TYPE_CHECKING, Any

# Avoid importing heavy optional dependency at module import time. Use a
# lightweight type stub for static checkers and perform runtime import when
# needed inside functions.
if TYPE_CHECKING:
    # Provide minimal stubs for type checkers so editors don't require the
    # real `python-pptx` package to resolve types.
    class Presentation:  # type: ignore
        pass

    class MSO_SHAPE_TYPE:  # type: ignore
        PICTURE: int
        TABLE: int
        PLACEHOLDER: int


def analyze_pptx(pptx_path: Path) -> dict:
    """Analyze a .pptx file and return a JSON-serializable summary.

    Returns a dict with keys: file, slides, slides_summary or an error dict.
    """
    try:
        import importlib

        pptx_mod = importlib.import_module("pptx")
        Presentation = getattr(pptx_mod, "Presentation")
        shapes_mod = importlib.import_module("pptx.enum.shapes")
        MSO_SHAPE_TYPE = getattr(shapes_mod, "MSO_SHAPE_TYPE")
    except Exception as e:
        return {"error": f"Missing dependency python-pptx: {e}. Install with `pip install python-pptx`."}

    if not pptx_path.exists():
        return {"error": f"File not found: {pptx_path}"}

    try:
        prs = Presentation(str(pptx_path))
    except Exception as e:
        return {"error": f"Failed to open PPTX: {e}"}

    slides_summary = []
    for i, slide in enumerate(prs.slides, start=1):
        title = None
        bullets = []
        images = 0
        tables = 0
        charts = 0

        # Title
        try:
            if getattr(slide.shapes, 'title', None) and slide.shapes.title.has_text_frame:
                title = slide.shapes.title.text.strip() or None
        except Exception:
            title = None

        # Collect text from all shapes
        for shp in slide.shapes:
            try:
                if getattr(shp, 'shape_type', None) == MSO_SHAPE_TYPE.PICTURE:
                    images += 1
                elif getattr(shp, 'shape_type', None) == MSO_SHAPE_TYPE.TABLE:
                    tables += 1
                elif getattr(shp, 'shape_type', None) == MSO_SHAPE_TYPE.PLACEHOLDER and hasattr(shp, 'chart'):
                    charts += 1

                if hasattr(shp, 'has_text_frame') and shp.has_text_frame and hasattr(shp, 'text_frame'):
                    text = '\n'.join(p.text for p in shp.text_frame.paragraphs).strip()  # type: ignore
                    if not text:
                        continue
                    if title and text == title:
                        continue
                    for line in [l.strip() for l in text.splitlines() if l.strip()]:
                        bullets.append(line)
            except Exception:
                continue

        # Notes
        notes = None
        try:
            if getattr(slide, 'has_notes_slide', False) and slide.notes_slide and slide.notes_slide.notes_text_frame:
                notes_text = slide.notes_slide.notes_text_frame.text
                notes = notes_text.strip() or None
        except Exception:
            notes = None

        slides_summary.append({
            "index": i,
            "title": title,
            "bullets": bullets[:20],
            "counts": {"images": images, "tables": tables, "charts": charts},
            "notes": notes,
        })

    return {
        "file": str(pptx_path),
        "slides": len(prs.slides),
        "slides_summary": slides_summary,
    }


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: python analyze_ppt.py <path-to-pptx>")
        sys.exit(2)

    pptx_path = Path(sys.argv[1])
    result = analyze_pptx(pptx_path)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
