from pathlib import Path
from typing import Optional


def find_data_file(repo_root: Path, name: str) -> Optional[Path]:
    """Find a dataset file by name in a few common locations.

    Search order:
    - repo_root / name
    - repo_root / 'data' / name
    - repo_root / 'AGRISENSEFULL-STACK' / name
    - repo_root / 'AGRISENSEFULL-STACK' / 'data' / name
    Returns Path if found, otherwise None.
    """
    candidates = [
        repo_root / name,
        repo_root / "data" / name,
        repo_root / "AGRISENSEFULL-STACK" / name,
        repo_root / "AGRISENSEFULL-STACK" / "data" / name,
    ]
    for p in candidates:
        if p.exists():
            return p
    return None
