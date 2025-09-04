import os
import streamlit as st
from .rag import Retriever, synthesize_answer

STORAGE_DIR = os.environ.get("RAG_STORAGE_DIR", "storage")
INDEX_PATH = os.path.join(STORAGE_DIR, "index.faiss")
META_PATH = os.path.join(STORAGE_DIR, "meta.json")
MODEL_NAME_FILE = os.path.join(STORAGE_DIR, "model_name.txt")

st.set_page_config(page_title="RAG Q/A Chatbot", page_icon="🌾", layout="centered")
st.title("🌾 RAG Q/A Chatbot")
st.caption("Embeddings + FAISS retrieval. Optional LLM synthesis if OPENAI_API_KEY is set.")

if not (os.path.exists(INDEX_PATH) and os.path.exists(META_PATH) and os.path.exists(MODEL_NAME_FILE)):
    st.error("Index not found. Run: `python -m src.ingest --csv data/dataset.csv --text-cols question answer`")
    st.stop()

with open(MODEL_NAME_FILE, "r", encoding="utf-8") as f:
    model_name = f.read().strip()

with st.sidebar:
    st.header("Settings")
    top_k = st.slider("Top-K documents", 1, 10, 3)
    synth = st.checkbox("Use LLM synthesis (requires OPENAI_API_KEY)", value=False)

retriever = Retriever(INDEX_PATH, META_PATH, model_name)

if "history" not in st.session_state:
    st.session_state.history = []

q = st.text_input("Ask a question")
if st.button("Ask") and q.strip():
    hits = retriever.search(q, top_k=top_k)
    if not hits:
        st.info("No results found. Try rephrasing.")
    else:
        if synth:
            ans = synthesize_answer(q, hits)
        else:
            ans = hits[0][1].get("answer", "(no 'answer' field)")  # best direct answer
        st.subheader("Answer")
        st.write(ans)

        st.subheader("Retrieved context")
        for score, row in hits:
            st.markdown(f"**Score:** {score:.3f}")
            if "question" in row: st.write(f"Q: {row['question']}")
            if "answer" in row: st.write(f"A: {row['answer']}")
            with st.expander("Row metadata"):
                st.json(row)
            st.divider()

        st.session_state.history.append({"q": q, "a": ans})

if st.session_state.history:
    st.subheader("History")
    for turn in reversed(st.session_state.history[-10:]):
        st.write(f"**Q:** {turn['q']}")
        st.write(f"**A:** {turn['a']}")