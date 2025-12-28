# 🔧 AgriSense GenAI Integration Quick Reference

## Files Created

### 1. Backend AI Core Modules

```
agrisense_app/backend/
├── core/
│   └── ai/
│       ├── __init__.py           # AI module exports
│       ├── rag_engine.py         # RAG chatbot (FarmerAssistant)
│       └── vision_engine.py      # VLM analyst (CropVisionAnalyst)
├── api/
│   └── ai_routes.py              # FastAPI routes for AI endpoints
└── requirements-ai.txt           # AI dependencies
```

### 2. Integration in main.py

**Location:** Lines 755-785 in `agrisense_app/backend/main.py`

**What was added:**
```python
# Include GenAI (RAG Chatbot + VLM Vision) API router
try:
    if __package__:
        from .api.ai_routes import router as ai_router
    else:
        from api.ai_routes import router as ai_router
    
    app.include_router(ai_router)
    logger.info("✅ GenAI API router included successfully - RAG Chatbot & VLM available at /ai/*")
    # ... logging for each endpoint
except ImportError as e:
    logger.warning(f"⚠️ GenAI API not available: {e}")
    # GenAI API optional - continue without it
    pass
```

**Why this location:**
- After VLM router inclusion (line 755)
- Before Flask storage server mount (line 787)
- Consistent with other router inclusions
- Non-blocking error handling (graceful degradation)

---

## API Endpoints Added

### Base Path: `/ai`

| Method | Endpoint | Description | Request Body | Response |
|--------|----------|-------------|--------------|----------|
| `POST` | `/ai/chat` | RAG-based farmer Q&A | `ChatRequest` | `ChatResponse` |
| `POST` | `/ai/analyze` | VLM crop image analysis | `multipart/form-data` | `AnalyzeResponse` |
| `POST` | `/ai/ingest` | Trigger knowledge base ingestion | `IngestRequest` | `Dict[stats]` |
| `GET` | `/ai/stats` | AI system statistics | - | `StatsResponse` |
| `GET` | `/ai/health` | AI services health check | - | `Dict[status]` |

---

## Usage Examples

### 1. RAG Chatbot

**Python (using requests):**
```python
import requests

response = requests.post(
    "http://localhost:8004/ai/chat",
    json={
        "query": "What are the best irrigation practices for wheat in dry climates?",
        "return_sources": True
    }
)

result = response.json()
print(f"Answer: {result['answer']}")
print(f"Confidence: {result['confidence']}")
print(f"Mode: {result['retrieval_mode']}")

if result.get('sources'):
    for source in result['sources']:
        print(f"Source: {source['metadata']}")
```

**JavaScript (using fetch):**
```javascript
const response = await fetch('http://localhost:8004/ai/chat', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    query: "How do I control aphids on crops?",
    return_sources: false
  })
});

const result = await response.json();
console.log('Answer:', result.answer);
console.log('Confidence:', result.confidence);
```

**cURL:**
```bash
curl -X POST http://localhost:8004/ai/chat \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What causes yellowing of rice leaves?",
    "return_sources": true
  }'
```

### 2. VLM Image Analysis

**Python (with image file):**
```python
import requests

with open('tomato_leaf.jpg', 'rb') as f:
    response = requests.post(
        "http://localhost:8004/ai/analyze",
        files={'file': ('tomato_leaf.jpg', f, 'image/jpeg')},
        data={'task': 'disease'}
    )

result = response.json()
print(f"Diagnosis: {result['diagnosis']}")
print(f"Severity: {result['severity']}")
print(f"Symptoms: {', '.join(result['symptoms'])}")
print(f"Treatment: {result['treatment']}")
```

**JavaScript (with file upload):**
```javascript
const formData = new FormData();
formData.append('file', fileInput.files[0]);
formData.append('task', 'disease');

const response = await fetch('http://localhost:8004/ai/analyze', {
  method: 'POST',
  body: formData
});

const result = await response.json();
console.log('Diagnosis:', result.diagnosis);
console.log('Treatment:', result.treatment);
```

**cURL:**
```bash
curl -X POST http://localhost:8004/ai/analyze \
  -F "file=@crop_image.jpg" \
  -F "task=weed"
```

### 3. Knowledge Base Ingestion

**Python:**
```python
import requests

response = requests.post(
    "http://localhost:8004/ai/ingest",
    json={
        "pdf_dir": "./crop_guides",
        "json_path": "./chatbot_qa_pairs.json",
        "force_rebuild": False
    }
)

stats = response.json()
print(f"Status: {stats['status']}")
print(f"PDFs loaded: {stats['pdfs_loaded']}")
print(f"QA pairs: {stats['json_pairs_loaded']}")
print(f"Total chunks: {stats['total_chunks']}")
```

**cURL:**
```bash
curl -X POST http://localhost:8004/ai/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "pdf_dir": "./crop_guides",
    "json_path": "./chatbot_qa_pairs.json",
    "force_rebuild": true
  }'
```

### 4. Check AI Status

**cURL:**
```bash
curl http://localhost:8004/ai/stats | jq '.'
```

**Expected output:**
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
    "memory_gb": 7.2
  }
}
```

---

## Dependency Injection Pattern

Both AI engines use singleton pattern for efficiency:

**RAG Engine:**
```python
from core.ai.rag_engine import get_farmer_assistant

@router.post("/ai/chat")
async def chat_endpoint(
    request: ChatRequest,
    assistant: FarmerAssistant = Depends(get_farmer_assistant)
):
    return assistant.ask(request.query)
```

**VLM Engine:**
```python
from core.ai.vision_engine import get_crop_vision_analyst

@router.post("/ai/analyze")
async def analyze_endpoint(
    file: UploadFile,
    analyst: CropVisionAnalyst = Depends(get_crop_vision_analyst)
):
    image_bytes = await file.read()
    return analyst.analyze_image(image_bytes)
```

**Why singleton:**
- Models are expensive to load (14GB for VLM)
- Embeddings are cached in memory
- Shared across all requests
- Reduces latency and memory footprint

---

## Environment Variables

Create `.env` in `agrisense_app/backend/`:

```bash
# Device selection (auto-detects if not set)
AGRISENSE_AI_DEVICE=cuda              # or "cpu"

# RAG Chatbot
AGRISENSE_CHROMA_DIR=./chroma_db      # Vector store location
AGRISENSE_LLM_MODEL=mistral           # Ollama model name
AGRISENSE_LLM_BACKEND=ollama          # or "llamacpp"

# VLM
AGRISENSE_VLM_MODEL=llava-hf/llava-v1.6-mistral-7b-hf
AGRISENSE_VLM_4BIT=true               # Use 4-bit quantization
AGRISENSE_MODEL_CACHE=./model_cache   # Model download cache

# Knowledge Base
AGRISENSE_PDF_DIR=./crop_guides
AGRISENSE_QA_JSON=./chatbot_qa_pairs.json
```

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                        AgriSense API                        │
│                      (FastAPI main.py)                      │
└─────────────────────────────────────────────────────────────┘
                              │
                              │ includes router
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    AI Routes (/ai)                          │
│                   (api/ai_routes.py)                        │
│                                                             │
│  POST /ai/chat      ──┐                                    │
│  POST /ai/analyze   ──┼──► Dependency Injection            │
│  POST /ai/ingest    ──┤                                    │
│  GET  /ai/stats     ──┘                                    │
└─────────────────────────────────────────────────────────────┘
                    │                    │
                    │                    │
                    ▼                    ▼
    ┌───────────────────────┐   ┌──────────────────────┐
    │   FarmerAssistant     │   │  CropVisionAnalyst   │
    │   (rag_engine.py)     │   │  (vision_engine.py)  │
    │                       │   │                      │
    │ • ChromaDB vector DB  │   │ • LLaVA-v1.6-7B VLM  │
    │ • Sentence-transformers│   │ • 4-bit quantization│
    │ • Ollama/LlamaCpp LLM │   │ • CUDA acceleration  │
    │ • PDF + JSON ingestion│   │ • Image preprocessing│
    └───────────────────────┘   └──────────────────────┘
             │                            │
             ▼                            ▼
    ┌──────────────┐              ┌─────────────┐
    │  ChromaDB    │              │ GPU Memory  │
    │  ./chroma_db │              │ ~8GB VRAM   │
    └──────────────┘              └─────────────┘
```

---

## Error Handling

All endpoints return structured errors:

**503 Service Unavailable:**
```json
{
  "detail": "AI services unavailable. Install requirements-ai.txt and initialize knowledge base."
}
```

**400 Bad Request:**
```json
{
  "detail": "Invalid file type: application/pdf. Allowed: image/jpeg, image/png, image/jpg, image/webp"
}
```

**500 Internal Server Error:**
```json
{
  "detail": "Failed to process query: CUDA out of memory"
}
```

**Graceful Degradation:**
- If dependencies not installed: API endpoints return 503
- If LLM unavailable: RAG falls back to retrieval-only mode
- Backend continues to function without AI features

---

## Testing Checklist

### ✅ Installation
- [ ] `pip install -r requirements-ai.txt` completed
- [ ] Ollama installed and running
- [ ] Model pulled: `ollama pull mistral`
- [ ] Environment variables set in `.env`

### ✅ RAG Chatbot
- [ ] Knowledge base directory exists: `./crop_guides/`
- [ ] PDFs added to knowledge base
- [ ] Ingestion completed: `POST /ai/ingest`
- [ ] ChromaDB created: `./chroma_db/` exists
- [ ] Chat query works: `POST /ai/chat`
- [ ] Sources returned when requested

### ✅ VLM Image Analysis
- [ ] Model downloaded to cache: `./model_cache/`
- [ ] CUDA available: `curl /ai/stats` shows "cuda"
- [ ] Image upload works: `POST /ai/analyze`
- [ ] Diagnosis returned with treatment
- [ ] Processing time acceptable (<10s on GPU)

### ✅ Integration
- [ ] Backend starts without errors
- [ ] Logs show: "✅ GenAI API router included successfully"
- [ ] OpenAPI docs show AI endpoints: http://localhost:8004/docs
- [ ] Health check passes: `GET /ai/health`
- [ ] Stats endpoint works: `GET /ai/stats`

---

## Quick Start Commands

```bash
# 1. Install dependencies
cd agrisense_app/backend
pip install -r requirements-ai.txt

# 2. Install Ollama and pull model
ollama pull mistral

# 3. Set environment variables
cp .env.example .env
# Edit .env with your settings

# 4. Create directories
mkdir -p crop_guides chroma_db model_cache

# 5. Add PDF crop guides to crop_guides/

# 6. Start backend
uvicorn main:app --port 8004 --reload

# 7. Ingest knowledge base (in new terminal)
curl -X POST http://localhost:8004/ai/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "pdf_dir": "./crop_guides",
    "json_path": "./chatbot_qa_pairs.json",
    "force_rebuild": true
  }'

# 8. Test RAG chat
curl -X POST http://localhost:8004/ai/chat \
  -H "Content-Type: application/json" \
  -d '{"query": "How to grow tomatoes?"}'

# 9. Test VLM analysis (with an image)
curl -X POST http://localhost:8004/ai/analyze \
  -F "file=@test_image.jpg" \
  -F "task=disease"

# 10. Check stats
curl http://localhost:8004/ai/stats | jq
```

---

## Performance Tips

1. **First request is slow (cold start):**
   - VLM: 30-60 seconds (model loading)
   - RAG: 5-10 seconds (embeddings + vectorstore)
   - Subsequent requests: <5 seconds

2. **Memory optimization:**
   - Enable 4-bit quantization: `AGRISENSE_VLM_4BIT=true`
   - Use smaller embedding model
   - Limit ChromaDB cache size

3. **Speed optimization:**
   - Use GPU: `AGRISENSE_AI_DEVICE=cuda`
   - Keep backend running (avoid cold starts)
   - Implement caching for repeated queries

4. **Scaling:**
   - Deploy RAG and VLM as separate services
   - Use async processing (Celery)
   - Load balance across multiple GPUs
   - Cache results in Redis

---

## Common Issues & Solutions

| Issue | Solution |
|-------|----------|
| "ModuleNotFoundError: langchain" | `pip install -r requirements-ai.txt` |
| "CUDA out of memory" | Enable 4-bit quantization or use CPU |
| "Ollama connection refused" | Start Ollama: `ollama serve` |
| "ChromaDB collection not found" | Run ingestion: `POST /ai/ingest` |
| "VLM inference very slow" | Check device is CUDA: `GET /ai/stats` |
| "Low quality answers" | Add more PDFs, increase top_k |

---

**Last Updated:** December 3, 2025  
**Integration Status:** ✅ Complete  
**Tested With:** FastAPI 0.118.0, Python 3.9, CUDA 11.8
