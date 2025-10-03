"""Train a small TF Keras text encoder on QA pairs and produce chatbot artifacts.

The script trains a model that maps raw strings to L2-normalized embeddings using
Keras TextVectorization -> Embedding -> pooling -> Dense -> L2 norm. It uses a
margin-based contrastive loss with in-batch negative sampling.

Outputs (written to `agrisense_app/backend` by default):
 - `chatbot_question_encoder/` (SavedModel directory for backend TFSMLayer)
 - `chatbot_question_encoder.keras` (Keras model file used by some scripts)
 - `chatbot_q_index.npz` (question embeddings + questions)
 - `chatbot_index.npz` (answer embeddings + answers)
 - `chatbot_qa_pairs.json` (QA JSON with questions/answers)

Usage:
  .venv\\Scripts\\python.exe scripts\\train_chatbot_encoder.py --csv agrisense_app/backend/chatbot_merged_clean.csv

This is intentionally conservative (small model) to run on CPU in reasonable time.
"""
import argparse
import json
import os
from pathlib import Path
import random
import time
from typing import List

import numpy as np

import tensorflow as tf
from tensorflow.keras import layers  # type: ignore


def build_text_encoder(vocab_size=20000, seq_len=64, embed_dim=128, proj_dim=256):
    inp = layers.Input(shape=(), dtype=tf.string, name="text")
    tv = layers.TextVectorization(max_tokens=vocab_size, output_mode="int", output_sequence_length=seq_len)
    x = tv(inp)
    x = layers.Embedding(input_dim=vocab_size, output_dim=embed_dim, mask_zero=True)(x)
    x = layers.GlobalAveragePooling1D()(x)
    x = layers.Dense(proj_dim, activation="relu")(x)
    # L2 normalize for cosine similarity
    x = layers.Lambda(lambda t: tf.math.l2_normalize(t, axis=1), name="l2norm")(x)
    model = tf.keras.Model(inputs=inp, outputs=x)  # type: ignore
    return model, tv


def margin_ranking_loss(q_emb, pos_emb, neg_emb, margin=0.2):
    # q_emb, pos_emb, neg_emb are L2-normalized -> cosine = dot
    sim_pos = tf.reduce_sum(q_emb * pos_emb, axis=1)
    sim_neg = tf.reduce_sum(q_emb * neg_emb, axis=1)
    loss = tf.maximum(0.0, margin - sim_pos + sim_neg)
    return tf.reduce_mean(loss)


def train(args):
    csv_path = Path(args.csv)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    import pandas as pd

    df = pd.read_csv(csv_path)
    if "question" not in df.columns or "answer" not in df.columns:
        raise SystemExit("CSV must contain question and answer columns")

    questions = df["question"].fillna("").astype(str).tolist()
    answers = df["answer"].fillna("").astype(str).tolist()
    sources = df["source"].fillna("").astype(str).tolist() if "source" in df.columns else [""] * len(questions)

    n = len(questions)
    print(f"Loaded {n} QA pairs")

    # prepare optional BM25 hard-negative index
    use_bm25 = False
    bm25 = None
    tokenized_answers = None
    if args.hard_negatives and args.hard_negatives > 0:
        try:
            from rank_bm25 import BM25Okapi

            # simple whitespace tokenizer
            tokenized_answers = [a.lower().split() for a in answers]
            bm25 = BM25Okapi(tokenized_answers)
            use_bm25 = True
            print(f"BM25 hard-negative mining enabled (topk={args.hard_negatives})")
        except Exception as e:
            print("rank_bm25 not available or failed to initialize; falling back to in-batch negatives:", e)
            use_bm25 = False

    # Build model and adapt TextVectorization
    model, tv = build_text_encoder(vocab_size=args.vocab_size, seq_len=args.seq_len, embed_dim=args.embed_dim, proj_dim=args.proj_dim)
    print("Adapting TextVectorization on combined texts...")
    tv.adapt(questions + answers)

    # Compile not required; we'll use custom training loop
    optimizer = tf.keras.optimizers.Adam(learning_rate=args.lr)  # type: ignore

    indices = np.arange(n)

    # training loop
    batch_size = args.batch_size
    steps_per_epoch = max(1, n // batch_size)
    print(f"Training for {args.epochs} epochs, steps_per_epoch={steps_per_epoch}, batch_size={batch_size}")

    for epoch in range(1, args.epochs + 1):
        t0 = time.time()
        # shuffle indices and create negatives by rolling
        perm = np.random.permutation(indices)
        neg_perm = np.roll(perm, shift=1)

        epoch_loss = 0.0
        for i in range(0, n, batch_size):
            batch_idx = perm[i : i + batch_size]
            q_batch = [questions[j] for j in batch_idx]
            pos_batch = [answers[j] for j in batch_idx]

            # determine hard negatives: prefer BM25 top non-matching answer if enabled
            if use_bm25 and bm25 is not None:
                neg_batch = []
                for qidx in batch_idx:
                    q_text = questions[qidx]
                    q_tokens = q_text.lower().split()
                    try:
                        scores = bm25.get_scores(q_tokens)  # type: ignore
                        # argsort descending
                        cand = np.argsort(-scores)
                        # pick first candidate that is not the positive
                        picked = None
                        for c in cand[: max(10, args.hard_negatives * 3)]:
                            if int(c) != int(qidx):
                                picked = int(c)
                                break
                        if picked is None:
                            # fallback to rolled perm
                            picked = int(neg_perm[np.where(perm == qidx)[0][0]])
                    except Exception:
                        picked = int(neg_perm[np.where(perm == qidx)[0][0]])
                    neg_batch.append(answers[picked])
            else:
                neg_idx = neg_perm[i : i + batch_size]
                neg_batch = [answers[j] for j in neg_idx]

            with tf.GradientTape() as tape:
                q_emb = model(tf.constant(q_batch), training=True)
                pos_emb = model(tf.constant(pos_batch), training=True)
                neg_emb = model(tf.constant(neg_batch), training=True)
                loss = margin_ranking_loss(q_emb, pos_emb, neg_emb, margin=args.margin)
            grads = tape.gradient(loss, model.trainable_variables)
            optimizer.apply_gradients(zip(grads, model.trainable_variables))  # type: ignore
            epoch_loss += float(loss.numpy()) * len(q_batch)

        epoch_loss = epoch_loss / n
        dt = time.time() - t0
        print(f"Epoch {epoch}/{args.epochs} loss={epoch_loss:.4f} time={dt:.1f}s")

    # Save model as SavedModel directory and as .keras
    saved_dir = out_dir / "chatbot_question_encoder"
    saved_dir.mkdir(parents=True, exist_ok=True)
    print("Saving SavedModel to", saved_dir)
    # Keras3 changed model.save behavior; prefer model.export() when available
    try:
        if hasattr(model, "export"):
            print("Using model.export(...) for SavedModel format")
            model.export(str(saved_dir))
        else:
            print("Using tf.saved_model.save(...) for SavedModel format")
            tf.saved_model.save(model, str(saved_dir))
    except Exception as e:
        print("SavedModel export failed:", e)

    keras_path = out_dir / "chatbot_question_encoder.keras"
    print("Also saving Keras model to", keras_path)
    try:
        model.save(str(keras_path))
    except Exception as e:
        print("Failed to save .keras file:", e)

    # Compute embeddings for q and answers and save artifacts
    print("Computing embeddings for all questions and answers (batching)")
    q_embs = []
    a_embs = []
    B = args.eval_batch
    for i in range(0, n, B):
        q_batch = questions[i : i + B]
        a_batch = answers[i : i + B]
        # Use tf.constant(string_list) to avoid numpy unicode dtype conversion issues
        q_embs.append(model.predict(tf.constant(q_batch, dtype=tf.string), verbose=0))
        a_embs.append(model.predict(tf.constant(a_batch, dtype=tf.string), verbose=0))
    q_embs = np.vstack(q_embs).astype(np.float32)
    a_embs = np.vstack(a_embs).astype(np.float32)

    # Ensure L2-normalized
    def l2norm(x):
        nrm = np.linalg.norm(x, axis=1, keepdims=True)
        nrm[nrm == 0] = 1.0
        return x / nrm

    q_embs = l2norm(q_embs)
    a_embs = l2norm(a_embs)

    q_index_path = out_dir / "chatbot_q_index.npz"
    idx_path = out_dir / "chatbot_index.npz"
    qa_json_path = out_dir / "chatbot_qa_pairs.json"

    print("Saving question index to", q_index_path)
    np.savez_compressed(q_index_path, embeddings=q_embs, questions=np.array(questions, dtype=object))
    print("Saving answer index to", idx_path)
    np.savez_compressed(idx_path, embeddings=a_embs, answers=np.array(answers, dtype=object))

    print("Saving QA pairs JSON to", qa_json_path)
    qa_meta = {"questions": list(questions), "answers": list(answers)}
    try:
        if sources and len(sources) == len(questions):
            qa_meta["sources"] = list(sources)
    except Exception:
        pass
    with qa_json_path.open("w", encoding="utf-8") as f:
        json.dump(qa_meta, f, ensure_ascii=False, indent=2)

    print("Training and artifact generation complete.")


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--csv", required=True)
    p.add_argument("--out-dir", default="agrisense_app/backend")
    p.add_argument("--epochs", type=int, default=8)
    p.add_argument("--batch-size", type=int, default=32)
    p.add_argument("--eval-batch", type=int, default=256)
    p.add_argument("--hard-negatives", type=int, default=0,
                   help="If >0, use BM25 to mine hard negatives per query (requires rank_bm25).")
    p.add_argument("--vocab-size", type=int, default=20000)
    p.add_argument("--seq-len", type=int, default=64)
    p.add_argument("--embed-dim", type=int, default=128)
    p.add_argument("--proj-dim", type=int, default=256)
    p.add_argument("--lr", type=float, default=1e-3)
    p.add_argument("--margin", type=float, default=0.2)
    return p.parse_args()


if __name__ == "__main__":
    args = parse_args()
    train(args)
