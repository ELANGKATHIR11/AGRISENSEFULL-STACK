# 🤖 AgriSense GenAI Setup Guide

## Overview

This guide walks you through setting up the GenAI features in AgriSense:
1. **RAG Chatbot**: LangChain-based farmer assistant with ChromaDB
2. **Crop Vision Analyst**: LLaVA VLM for disease/weed detection

---

## 📋 Prerequisites

### Hardware Requirements

**For RAG Chatbot (CPU works fine):**
- RAM: 8GB minimum, 16GB recommended
- Storage: 2GB for embeddings + vector store
- GPU: Optional (speeds up embeddings)

**For VLM Vision Analyst (GPU recommended):**
- RAM: 16GB minimum
- VRAM: 8GB+ GPU (with 4-bit quantization)
- Storage: 15GB for model cache
- GPU: CUDA-capable GPU strongly recommended
  - Without GPU: Will run on CPU (very slow ~2-5 min per image)
  - With GPU: Fast inference (~2-5 seconds per image)

### Software Requirements

- Python 3.9+
- CUDA 11.8+ (if using GPU)
- Ollama (optional, for local LLM management)

---

## 🚀 Installation Steps

### Step 1: Install AI Dependencies

```bash
cd agrisense_app/backend
pip install -r requirements-ai.txt
```

**What this installs:**
- LangChain ecosystem (langchain, langchain-community, langchain-core)
- ChromaDB for vector storage
- Sentence-transformers for embeddings
- Ollama/LlamaCpp for local LLM
- PyTorch, Transformers, BitsAndBytes for VLM
- PDF loaders (pypdf, pdfplumber)

### Step 2: Install Ollama (Recommended for RAG)

**Why Ollama?** Easiest way to run local LLMs without manual model management.

**Installation:**

**Windows:**
```powershell
# Download from: https://ollama.ai/download
# Or via Chocolatey:
choco install ollama
```

**Linux:**
```bash
curl -fsSL https://ollama.ai/install.sh | sh
```

**macOS:**
```bash
brew install ollama
```

**Pull a model:**
```bash
# Option 1: Mistral (7B, recommended)
ollama pull mistral

# Option 2: Llama2 (7B, also good)
ollama pull llama2

# Option 3: Smaller/faster models
ollama pull phi
```

### Step 3: Set Environment Variables

Create `.env` file in `agrisense_app/backend/`:

```bash
# ===== GenAI Configuration =====

# Device selection (auto-detects if not set)
AGRISENSE_AI_DEVICE=cuda  # or "cpu"

# RAG Chatbot Settings
AGRISENSE_CHROMA_DIR=./chroma_db
AGRISENSE_LLM_MODEL=mistral  # or "llama2", "phi"
AGRISENSE_LLM_BACKEND=ollama  # or "llamacpp"

# VLM Settings
AGRISENSE_VLM_MODEL=llava-hf/llava-v1.6-mistral-7b-hf
AGRISENSE_VLM_4BIT=true  # Use 4-bit quantization (saves memory)
AGRISENSE_MODEL_CACHE=./model_cache

# Knowledge Base Paths
AGRISENSE_PDF_DIR=./crop_guides  # Directory with PDF manuals
AGRISENSE_QA_JSON=./chatbot_qa_pairs.json  # Existing QA pairs
```

### Step 4: Prepare Knowledge Base

**Create directory structure:**
```bash
cd agrisense_app/backend
mkdir -p crop_guides chroma_db model_cache
```

**Add crop guides:**
- Place PDF files in `crop_guides/` directory
- PDFs should contain agricultural knowledge (crop cultivation, diseases, treatments)
- Example structure:
  ```
  crop_guides/
  ├── tomato_cultivation.pdf
  ├── wheat_diseases.pdf
  ├── irrigation_guide.pdf
  └── fertilizer_recommendations.pdf
  ```

**Existing QA pairs:**
- Your `chatbot_qa_pairs.json` will be automatically loaded
- No changes needed to existing file

### Step 5: Initial Knowledge Base Ingestion

**Option A: Using API endpoint (Recommended)**

Start the backend:
```bash
uvicorn main:app --port 8004
```

Trigger ingestion:
```bash
curl -X POST http://localhost:8004/ai/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "pdf_dir": "./crop_guides",
    "json_path": "./chatbot_qa_pairs.json",
    "force_rebuild": true
  }'
```

**Option B: Using Python script**

Create `scripts/ingest_knowledge_base.py`:
```python
import os
import sys

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'agrisense_app', 'backend'))

from core.ai.rag_engine import FarmerAssistant

def main():
    assistant = FarmerAssistant(
        chroma_persist_dir="./chroma_db",
        llm_model="mistral",
    )
    
    stats = assistant.ingest_knowledge_base(
        pdf_dir="./crop_guides",
        json_path="./chatbot_qa_pairs.json",
        force_rebuild=True,
    )
    
    print(f"Ingestion complete!")
    print(f"PDFs loaded: {stats.get('pdfs_loaded', 0)}")
    print(f"QA pairs loaded: {stats.get('json_pairs_loaded', 0)}")
    print(f"Total chunks: {stats.get('total_chunks', 0)}")

if __name__ == "__main__":
    main()
```

Run:
```bash
python scripts/ingest_knowledge_base.py
```

---

## 🧪 Testing the Setup

### Test RAG Chatbot

```bash
curl -X POST http://localhost:8004/ai/chat \
  -H "Content-Type: application/json" \
  -d '{
    "query": "How do I treat tomato blight?",
    "return_sources": true
  }'
```

**Expected response:**
```json
{
  "answer": "To treat tomato blight, follow these steps...",
  "confidence": 0.92,
  "retrieval_mode": "rag",
  "sources": [
    {
      "content": "Tomato blight treatment guide...",
      "metadata": {"source": "tomato_diseases.pdf", "page": 5}
    }
  ]
}
```

### Test VLM Image Analysis

```bash
# Using a test image
curl -X POST http://localhost:8004/ai/analyze \
  -F "file=@test_images/tomato_leaf.jpg" \
  -F "task=disease"
```

**Expected response:**
```json
{
  "diagnosis": "Early Blight (Alternaria solani)",
  "severity": "mild",
  "symptoms": [
    "Dark concentric rings on lower leaves",
    "Yellowing around spots"
  ],
  "treatment": "Apply copper-based fungicide. Remove affected leaves.",
  "confidence": 0.87,
  "task": "disease",
  "raw_output": "This tomato plant shows early signs..."
}
```

### Test AI Stats

```bash
curl http://localhost:8004/ai/stats
```

**Expected response:**
```json
{
  "rag_available": true,
  "vlm_available": true,
  "rag_stats": {
    "device": "cuda",
    "llm_available": true,
    "vectorstore_initialized": true,
    "documents_count": 1547
  },
  "vlm_stats": {
    "model_name": "llava-hf/llava-v1.6-mistral-7b-hf",
    "device": "cuda",
    "memory_gb": 7.2,
    "cuda_device_name": "NVIDIA GeForce RTX 3080"
  }
}
```

---

## 🔧 Configuration Options

### RAG Chatbot Fine-Tuning

**In `core/ai/rag_engine.py`, adjust:**

```python
assistant = FarmerAssistant(
    chunk_size=1000,        # Increase for longer context
    chunk_overlap=200,      # Increase to prevent info loss
    top_k=4,               # More docs = better context
    embedding_model="...",  # Change embedding model
)
```

**Embedding model options:**
- `sentence-transformers/all-MiniLM-L6-v2` (default, fast, lightweight)
- `sentence-transformers/all-mpnet-base-v2` (better quality, slower)
- `sentence-transformers/multi-qa-MiniLM-L6-cos-v1` (optimized for Q&A)

### VLM Fine-Tuning

**In `core/ai/vision_engine.py`, adjust:**

```python
analyst = CropVisionAnalyst(
    use_4bit=True,              # False for full precision (needs 28GB VRAM)
    device="cuda",              # or "cpu"
)

# During analysis:
result = analyst.analyze_image(
    image_bytes,
    max_new_tokens=512,         # Increase for longer explanations
    temperature=0.2,            # Lower = more deterministic
)
```

---

## 🐛 Troubleshooting

### Issue: "CUDA out of memory"

**Solution:**
1. Enable 4-bit quantization: `AGRISENSE_VLM_4BIT=true`
2. Reduce batch size (not exposed in API yet)
3. Use smaller VLM model (not recommended, lower quality)
4. Close other GPU applications
5. Fallback to CPU: `AGRISENSE_AI_DEVICE=cpu`

### Issue: "Ollama connection refused"

**Solution:**
1. Check Ollama is running: `ollama serve`
2. Verify model is pulled: `ollama list`
3. Pull model if missing: `ollama pull mistral`
4. Check Ollama port (default 11434): `curl http://localhost:11434/api/tags`

### Issue: "ChromaDB collection already exists"

**Solution:**
1. Delete existing ChromaDB: `rm -rf ./chroma_db`
2. Re-run ingestion with `force_rebuild=true`

### Issue: VLM inference is very slow

**Check:**
- Device: `curl http://localhost:8004/ai/stats` (should show "cuda")
- GPU usage: `nvidia-smi` (should show model loaded)
- 4-bit quantization enabled: Check VLM stats

**If on CPU:**
- Expected: 2-5 minutes per image
- Consider cloud deployment with GPU

### Issue: "ModuleNotFoundError: No module named 'langchain'"

**Solution:**
```bash
pip install -r requirements-ai.txt
```

### Issue: Low quality RAG answers

**Solutions:**
1. Increase `top_k` (retrieve more context)
2. Use better embedding model
3. Add more PDFs to knowledge base
4. Improve PDF quality (OCR if scanned)
5. Adjust LLM temperature (lower = more factual)

---

## 📊 Performance Benchmarks

**RAG Chatbot (with Ollama Mistral 7B):**
- First query: ~3-5 seconds (cold start)
- Subsequent queries: ~1-2 seconds
- Memory: ~4GB RAM (embeddings + ChromaDB)

**VLM Image Analysis (with 4-bit quantization):**
- GPU (RTX 3080): 2-5 seconds per image
- CPU (i7-12700K): 120-300 seconds per image
- Memory: ~8GB VRAM (GPU) or ~12GB RAM (CPU)

---

## 🔐 Production Deployment

### Security Considerations

1. **Add authentication to `/ai/ingest`:**
```python
from fastapi import Depends
from your_auth import verify_admin

@router.post("/ingest", dependencies=[Depends(verify_admin)])
async def ingest_knowledge_base(...):
    ...
```

2. **Rate limiting:**
```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@router.post("/ai/chat")
@limiter.limit("10/minute")  # 10 requests per minute
async def chat_with_assistant(...):
    ...
```

3. **Environment variables:**
- Store sensitive config in `.env` (not in git)
- Use secrets management (AWS Secrets Manager, Azure Key Vault)

### Scaling Considerations

**For high traffic:**
1. Deploy RAG and VLM as separate microservices
2. Use message queue (Celery) for async processing
3. Implement result caching (Redis)
4. Load balance across multiple GPU instances

**Example Celery task for VLM:**
```python
from celery import Celery

celery_app = Celery('agrisense', broker='redis://localhost:6379/0')

@celery_app.task
def analyze_image_async(image_bytes: bytes, task: str):
    analyst = get_crop_vision_analyst()
    return analyst.analyze_image(image_bytes, task)
```

---

## 📚 API Documentation

Once the backend is running, visit:
- **Interactive docs**: http://localhost:8004/docs
- **ReDoc**: http://localhost:8004/redoc

All AI endpoints are documented with:
- Request/response schemas
- Example payloads
- Try-it-out functionality

---

## 🎯 Next Steps

1. **Enhance RAG:**
   - Add more PDF crop guides
   - Fine-tune embedding model on agricultural text
   - Implement hybrid search (semantic + keyword)
   - Add conversation memory

2. **Enhance VLM:**
   - Fine-tune on agricultural images
   - Add batch processing endpoint
   - Implement image preprocessing pipeline
   - Add confidence calibration

3. **Frontend Integration:**
   - Create chat interface for RAG
   - Add image upload widget for VLM
   - Display source citations
   - Show confidence scores

4. **Monitoring:**
   - Add Prometheus metrics
   - Track query latency
   - Monitor model performance
   - Alert on errors

---

## 📞 Support

For issues or questions:
1. Check logs: `tail -f agrisense_app/backend/uvicorn.log`
2. Review error traces in API responses
3. Test with `curl` to isolate frontend vs backend issues
4. Check GPU with `nvidia-smi`
5. Verify Ollama with `ollama list`

---

**Last Updated:** December 2025  
**Tested On:** Python 3.9, CUDA 11.8, Ubuntu 22.04 / Windows 11
