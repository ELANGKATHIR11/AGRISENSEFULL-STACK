"""
LLM-powered QA augmentation: generate paraphrased questions for existing Q/A pairs.

Usage (PowerShell):
  .venv\\Scripts\\python.exe agrisense_app\\scripts\\augment_qa_with_llm.py \\
    --input "agriculture-qa-english-only/data/train-00000-of-00001.parquet" \\
    --output "AGRISENSEFULL-STACK/agrisense_app/backend/chatbot_augmented_qa.csv" \\
    --per_question 2 --max_records 2000

Environment variables used (set in agrisense_app/backend/.env if desired):
  GEMINI_API_KEY          -> prefer Gemini
  GEMINI_MODEL            -> default: gemini-1.5-flash-latest
  DEEPSEEK_API_KEY        -> fallback to DeepSeek
  DEEPSEEK_MODEL          -> default: deepseek-chat
  DEEPSEEK_BASE_URL       -> default: https://api.deepseek.com

Output CSV columns:
  id, parent_id, source, question, answer

Notes:
  - Keeps originals (source=original) and adds paraphrases (source=gemini/deepseek).
  - Skips questions that fail to paraphrase; continues.
  - If both keys are missing, exits with a message.
"""

from __future__ import annotations

import argparse
import csv
import os
import random
import sys
from dataclasses import dataclass
from typing import Iterable, List, Optional


def _try_import_pandas():
    try:
        import pandas as pd  # type: ignore

        return pd
    except Exception as e:
        print(f"[augment] pandas not available: {e}")
        return None


def _load_qa(input_path: str, max_records: Optional[int] = None):
    pd = _try_import_pandas()
    rows: List[dict] = []
    if pd is not None:
        try:
            if input_path.lower().endswith(".parquet"):
                df = pd.read_parquet(input_path)
            else:
                df = pd.read_csv(input_path)
            # Heuristic column mapping
            cols = {c.lower(): c for c in df.columns}
            qcol = cols.get("question") or cols.get("query") or list(df.columns)[0]
            acol = cols.get("answer") or cols.get("response") or list(df.columns)[1]
            for _, r in df.iterrows():
                q = str(r[qcol]).strip()
                a = str(r[acol]).strip()
                if q and a:
                    rows.append({"question": q, "answer": a})
        except Exception as e:
            print(
                f"[augment] Failed to load with pandas, falling back to CSV reader if possible: {e}"
            )

    if not rows:
        if not os.path.isfile(input_path):
            raise FileNotFoundError(f"Input file not found: {input_path}")
        # Simple CSV fallback (expects header with question,answer)
        with open(input_path, "r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            qkey = None
            akey = None
            lower_keys = {k.lower(): k for k in reader.fieldnames or []}
            qkey = lower_keys.get("question")
            akey = lower_keys.get("answer")
            if not qkey or not akey:
                raise ValueError(
                    "CSV must contain 'question' and 'answer' headers if pandas is unavailable."
                )
            for r in reader:
                q = (r.get(qkey) or "").strip()
                a = (r.get(akey) or "").strip()
                if q and a:
                    rows.append({"question": q, "answer": a})

    if max_records is not None:
        rows = rows[:max_records]
    return rows


# --- LLM Clients ---
def _use_gemini() -> bool:
    return bool(os.environ.get("GEMINI_API_KEY"))


def _use_deepseek() -> bool:
    return bool(os.environ.get("DEEPSEEK_API_KEY"))


def _gemini_paraphrase_batch(
    prompts: List[str], n: int, system_hint: str
) -> List[List[str]]:
    try:
        import google.generativeai as genai  # type: ignore
    except Exception:
        genai = None

    key = os.environ.get("GEMINI_API_KEY")
    model_name = os.environ.get("GEMINI_MODEL", "gemini-1.5-flash-latest")
    if genai is None:
        print("[augment] google.generativeai not available; cannot use Gemini")
        return [[] for _ in prompts]

    configure_fn = getattr(genai, "configure", None)
    GenerativeModel = getattr(genai, "GenerativeModel", None)

    if not key:
        print("[augment] GEMINI_API_KEY not set; cannot use Gemini")
        return [[] for _ in prompts]

    if configure_fn is None or GenerativeModel is None:
        print("[augment] Installed google.generativeai has incompatible API; cannot use Gemini")
        return [[] for _ in prompts]

    # Configure and instantiate model in a guarded way
    try:
        configure_fn(api_key=key)
        model = GenerativeModel(model_name, system_instruction=system_hint)
    except Exception as e:
        print(f"[augment] Failed to initialize Gemini model: {e}")
        return [[] for _ in prompts]

    outputs: List[List[str]] = []
    for q in prompts:
        try:
            content = (
                "You are a helpful data augmenter. Given the agricultural question, write "
                f"{n} diverse, concise paraphrases that keep the same meaning. Return JSON with key 'paraphrases' as a list of strings.\n"
                f"Question: {q}"
            )
            resp = model.generate_content(
                content, safety_settings=None, request_options={"timeout": 20}
            )
            text = (resp.text or "").strip()
            cands = _extract_list_from_json(text) or _split_lines(text)
            outs = [s for s in cands if s and s.lower() != q.lower()]
            outputs.append(outs[:n])
        except Exception as e:
            print(f"[augment] Gemini paraphrase failed, will fallback if possible: {e}")
            outputs.append([])
    return outputs


def _deepseek_paraphrase_batch(
    prompts: List[str], n: int, system_hint: str
) -> List[List[str]]:
    from openai import OpenAI  # type: ignore

    api_key = os.environ["DEEPSEEK_API_KEY"]
    base_url = os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
    model = os.environ.get("DEEPSEEK_MODEL", "deepseek-chat")
    client = OpenAI(api_key=api_key, base_url=base_url)
    outputs: List[List[str]] = []
    for q in prompts:
        try:
            prompt = (
                system_hint
                + "\n"
                + "You are a helpful data augmenter. Given the agricultural question, write "
                + f"{n} diverse, concise paraphrases that keep the same meaning. "
                + "Return JSON with key 'paraphrases' as a list of strings.\n"
                + f"Question: {q}"
            )
            resp = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_hint},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.7,
                timeout=20,
            )
            text = (resp.choices[0].message.content or "").strip()
            cands = _extract_list_from_json(text) or _split_lines(text)
            outs = [s for s in cands if s and s.lower() != q.lower()]
            outputs.append(outs[:n])
        except Exception as e:
            print(f"[augment] DeepSeek paraphrase failed: {e}")
            outputs.append([])
    return outputs


def _extract_list_from_json(text: str) -> Optional[List[str]]:
    import json

    try:
        # strip code fences if present
        if text.startswith("```"):
            text = text.strip().strip("`")
            # could be like json\n{...}
            if "\n" in text:
                text = text.split("\n", 1)[1]
        data = json.loads(text)
        if (
            isinstance(data, dict)
            and "paraphrases" in data
            and isinstance(data["paraphrases"], list)
        ):
            return [str(x).strip() for x in data["paraphrases"]]
        if isinstance(data, list):
            return [str(x).strip() for x in data]
    except Exception:
        pass
    return None


def _split_lines(text: str) -> List[str]:
    lines = [l.strip(" -\t\r\n") for l in text.splitlines()]
    return [l for l in lines if l]


@dataclass
class AugItem:
    id: int
    parent_id: int
    source: str  # original|gemini|deepseek
    question: str
    answer: str


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--input",
        required=False,
        default=os.path.join(
            "agriculture-qa-english-only", "data", "train-00000-of-00001.parquet"
        ),
    )
    parser.add_argument(
        "--output",
        required=False,
        default=os.path.join(
            "AGRISENSEFULL-STACK",
            "agrisense_app",
            "backend",
            "chatbot_augmented_qa.csv",
        ),
    )
    parser.add_argument("--per_question", type=int, default=2)
    parser.add_argument("--max_records", type=int, default=1000)
    parser.add_argument("--shuffle", action="store_true")
    args = parser.parse_args()

    # Try loading environment from backend .env if python-dotenv is installed
    try:
        from dotenv import load_dotenv  # type: ignore

        repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        backend_env = os.path.join(repo_root, "agrisense_app", "backend", ".env")
        if os.path.isfile(backend_env):
            load_dotenv(backend_env)
        elif os.path.isfile(".env"):
            load_dotenv(".env")
    except Exception:
        pass

    if not (_use_gemini() or _use_deepseek()):
        print(
            "[augment] No GEMINI_API_KEY or DEEPSEEK_API_KEY in environment. Aborting."
        )
        sys.exit(1)

    rows = _load_qa(args.input, max_records=args.max_records)
    if args.shuffle:
        random.shuffle(rows)
    print(f"[augment] Loaded {len(rows)} QA rows from {args.input}")

    system_hint = (
        "You are assisting with preparing training data for an agricultural QA retrieval model. "
        "Keep domain terms intact (crop names, fertilizer names, pests, etc.). Do not invent facts; paraphrase only."
    )

    items: List[AugItem] = []
    next_id = 1
    for idx, r in enumerate(rows, start=1):
        q = r["question"].strip()
        a = r["answer"].strip()
        parent_id = next_id
        items.append(
            AugItem(id=next_id, parent_id=0, source="original", question=q, answer=a)
        )
        next_id += 1

        paraphrases: List[str] = []
        # Try Gemini first for each question; fallback to DeepSeek if empty
        if _use_gemini():
            batches = _gemini_paraphrase_batch([q], args.per_question, system_hint)
            paraphrases = batches[0] if batches else []
        if not paraphrases and _use_deepseek():
            batches = _deepseek_paraphrase_batch([q], args.per_question, system_hint)
            paraphrases = batches[0] if batches else []

        for p in paraphrases:
            items.append(
                AugItem(
                    id=next_id,
                    parent_id=parent_id,
                    source=("gemini" if _use_gemini() else "deepseek"),
                    question=p,
                    answer=a,
                )
            )
            next_id += 1

        if idx % 50 == 0:
            print(
                f"[augment] Processed {idx}/{len(rows)} questions; total items so far: {len(items)}"
            )

    # Ensure output directory exists
    out_dir = os.path.dirname(args.output)
    if out_dir and not os.path.isdir(out_dir):
        os.makedirs(out_dir, exist_ok=True)

    with open(args.output, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["id", "parent_id", "source", "question", "answer"])
        for it in items:
            writer.writerow([it.id, it.parent_id, it.source, it.question, it.answer])
    print(f"[augment] Wrote {len(items)} rows to {args.output}")


if __name__ == "__main__":
    main()
