"""
Prepare KisanVaani agriculture QA CSV from the Hugging Face Parquet file.

This script:
- Loads the Parquet dataset at ../AGRISENSEFULL-STACK/agriculture-qa-english-only/data/train-00000-of-00001.parquet
- Ensures columns are named 'question' and 'answer'
- Adds a 'source' column with value 'KisanVaani'
- Writes CSV to the workspace root as 'KisanVaani_agriculture_qa.csv'

Usage (Windows PowerShell):
  <repo>/.venv/Scripts/python.exe AGRISENSEFULL-STACK/scripts/prepare_kisan_qa_csv.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd


def main() -> int:
    # Determine paths
    script_path = Path(__file__).resolve()
    workspace_root = script_path.parents[2]  # .../AGRISENSE FULL-STACK
    parquet_path = (
        workspace_root
        / "AGRISENSEFULL-STACK/agriculture-qa-english-only"
        / "data"
        / "train-00000-of-00001.parquet"
    )
    output_csv = workspace_root / "KisanVaani_agriculture_qa.csv"

    if not parquet_path.exists():
        print(f"Parquet file not found: {parquet_path}")
        return 1

    print(f"Loading Parquet: {parquet_path}")
    try:
        df = pd.read_parquet(parquet_path)
    except Exception as e:
        print(
            "Failed to read Parquet. Ensure a Parquet engine (pyarrow or fastparquet) is installed."
        )
        print(f"Error: {e}")
        return 1

    # Normalize columns
    cols_lower = {c.lower(): c for c in df.columns}
    q_col = (
        cols_lower.get("question") or cols_lower.get("ques") or cols_lower.get("query")
    )
    a_col = (
        cols_lower.get("answer")
        or cols_lower.get("answers")
        or cols_lower.get("ans")
        or cols_lower.get("response")
    )

    if q_col is None or a_col is None:
        print("Could not find 'question' and 'answer' columns in the dataset.")
        print(f"Available columns: {list(df.columns)}")
        return 1

    # Rename to standard names
    rename_map = {q_col: "question", a_col: "answer"}
    df = df.rename(columns=rename_map)

    # If we have an 'answers' style column that was renamed to 'answer', flatten to a string
    if "answer" in df.columns:

        def _to_answer(val):
            # Handle common shapes: list[str], list[dict], dict, str, None
            try:
                import math

                if val is None:
                    return ""
                # pandas may give NaN
                if isinstance(val, float) and math.isnan(val):
                    return ""
            except Exception:
                pass

            # list case
            if isinstance(val, (list, tuple)):
                if not val:
                    return ""
                first = val[0]
                if isinstance(first, dict):
                    # prefer 'text' or 'answer' key if present
                    for key in ("text", "answer", "value"):
                        if key in first and first[key] is not None:
                            return str(first[key])
                    # otherwise join stringified dicts
                    return "; ".join(
                        str(x.get("text") or x.get("answer") or x) for x in val
                    )
                # list of strings or primitives
                return str(first)

            # dict case
            if isinstance(val, dict):
                for key in ("text", "answer", "value"):
                    if key in val and val[key] is not None:
                        return str(val[key])
                # fallback to first value
                if val:
                    return str(next(iter(val.values())))
                return ""

            # already a string or other primitive
            return str(val)

        df["answer"] = df["answer"].map(_to_answer)

    # Keep only relevant columns if they exist; otherwise keep all
    keep_cols = [c for c in ["question", "answer"] if c in df.columns]
    if len(keep_cols) == 2:
        df = df[keep_cols]

    # Add source column
    df["source"] = "KisanVaani"

    # Write CSV
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_csv, index=False)
    print(f"Wrote CSV: {output_csv} ({len(df):,} rows)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
