from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import List, Tuple

import pandas as pd


def _norm_text(s: str) -> str:
    s = (s or "").strip()
    s = re.sub(r"\s+", " ", s)
    # remove duplicate trailing punctuation like ??? or !!!
    s = re.sub(r"([?.!])\1+\s*$", r"\1", s)
    return s


def _load_csv_if_exists(
    p: Path, q_keys: List[str], a_keys: List[str]
) -> pd.DataFrame | None:
    if not p.exists():
        return None
    try:
        df = pd.read_csv(p)
    except Exception:
        return None
    cols = {str(c).strip().lower(): c for c in df.columns}
    q = next((cols.get(k) for k in q_keys if k in cols), None)
    a = next((cols.get(k) for k in a_keys if k in cols), None)
    if not (q and a):
        return None
    out = df.rename(columns={q: "question", a: "answer"})[["question", "answer"]].copy()
    out["question"] = out["question"].astype(str).map(_norm_text)
    out["answer"] = out["answer"].astype(str).map(_norm_text)
    out = out[(out["question"] != "") & (out["answer"] != "")]
    return out


def load_all(repo_root: Path) -> List[Tuple[str, pd.DataFrame]]:
    roots = [repo_root, repo_root / "AGRISENSEFULL-STACK"]
    sources: list[Tuple[str, pd.DataFrame]] = []

    # KisanVaani
    for r in roots:
        df = _load_csv_if_exists(
            r / "KisanVaani_agriculture_qa.csv",
            q_keys=["question", "questions", "q"],
            a_keys=["answer", "answers", "a"],
        )
        if df is not None:
            sources.append(("KisanVaani", df))
            break

    # Soil QA
    for r in roots:
        df = _load_csv_if_exists(
            r
            / "Agriculture-Soil-QA-Pairs-Dataset"
            / "qna-dataset-farmgenie-soil-v2.csv",
            q_keys=[
                "question",
                "question.question",
                "question_text",
                "questions",
                "q",
                "QUESTION.question".lower(),
            ],
            a_keys=["answer", "answers", "a", "ANSWER".lower()],
        )
        if df is not None:
            sources.append(("SoilQA", df))
            break

    # Farming FAQ (both variants)
    for name in (
        "Farming_FAQ_Assistant_Dataset.csv",
        "Farming_FAQ_Assistant_Dataset (2).csv",
    ):
        for r in roots:
            df = _load_csv_if_exists(
                r / name,
                q_keys=["question", "questions", "q"],
                a_keys=["answer", "answers", "a"],
            )
            if df is not None:
                sources.append(("FarmingFAQ", df))

    # data_core.csv
    for r in roots:
        df = _load_csv_if_exists(
            r / "data_core.csv",
            q_keys=["question", "questions", "q"],
            a_keys=["answer", "answers", "a"],
        )
        if df is not None:
            sources.append(("DataCore", df))
            break

    return sources


def clean_merge(repo_root: Path, out_path: Path) -> Path:
    sources = load_all(repo_root)
    if not sources:
        raise SystemExit("No input QA CSVs found to clean/merge.")

    # Concatenate all
    df = pd.concat([d.assign(source=name) for name, d in sources], ignore_index=True)

    # Basic normalization already applied via _load_csv_if_exists
    # Remove stylistic quotes around answers
    df["answer"] = df["answer"].str.replace(r"^\"|\"$", "", regex=True)

    # Drop exact duplicates
    df.drop_duplicates(subset=["question", "answer"], inplace=True)

    # De-duplicate repeated questions: keep the longest informative answer
    df = (
        df.assign(ans_len=df["answer"].str.len())
        .sort_values(["question", "ans_len"], ascending=[True, False])
        .drop(columns=["ans_len"])  # type: ignore[arg-type]
        .drop_duplicates(subset=["question"], keep="first")
    )

    # Filter out very short/low-signal questions
    df = df[df["question"].str.len() >= 8]

    # Optional: remove obvious Q/A noise (simple heuristics)
    noise_q = {
        "where do i submit my answer?",
        "right here",
    }
    df = df[~df["question"].str.lower().isin(noise_q)]

    # Save
    out_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_path, index=False)
    # Write a brief report JSON alongside
    report = {
        "counts": {name: int(len(d)) for name, d in sources},
        "total_after_clean": int(len(df)),
        "out": str(out_path),
    }
    out_path.with_suffix(".report.json").write_text(json.dumps(report, indent=2))
    return out_path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--out",
        type=str,
        default="agrisense_app/backend/chatbot_merged_clean.csv",
        help="Output CSV path (relative to repo root)",
    )
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parents[1]
    out_path = (repo_root / args.out).resolve()
    final = clean_merge(repo_root, out_path)
    print(f"Wrote cleaned/merged QA -> {final}")


if __name__ == "__main__":
    main()
