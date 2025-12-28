# 🦙 Ollama LLM Integration Guide for AgriSense Chatbot

## Overview
This guide helps you integrate Ollama (a lightweight local LLM framework) with your AgriSense chatbot for **local, offline inference** without API costs.

---

## Step 1: Install Ollama

### Windows Installation
1. **Download Ollama for Windows**
   - Visit: https://ollama.ai/download
   - Download the Windows installer
   - Run the installer and follow prompts
   - Ollama will start automatically on port `11434`

2. **Verify Installation**
   ```powershell
   # Check if Ollama is running
   curl http://localhost:11434/api/tags
   
   # Should return: {"models": []}
   ```

3. **Alternative: Docker (if preferred)**
   ```powershell
   docker run -d -p 11434:11434 -v ollama:/root/.ollama ollama/ollama
   ```

---

## Step 2: Download a Lightweight LLM Model

### Recommended Models for Agriculture Chatbot

| Model | Size | Speed | Best For |
|-------|------|-------|----------|
| **Phi 2** | 1.4 GB | ⚡⚡⚡ Fast | Quick responses, resource-limited |
| **Mistral** | 4 GB | ⚡⚡ Good | Balanced quality & speed |
| **Neural Chat** | 2.7 GB | ⚡⚡ Good | Conversational, lightweight |
| **Llama 2** | 3.8 GB | ⚡⚡ Good | General purpose, reliable |
| **Tinyllama** | 637 MB | ⚡⚡⚡ Very Fast | Edge devices, minimal resources |

### Download Recommended Models

**Option 1: Phi 2 (RECOMMENDED - Fastest)**
```powershell
# Opens new terminal and downloads Phi 2 (~1.4 GB)
ollama pull phi
```

**Option 2: Mistral (Balanced)**
```powershell
ollama pull mistral
```

**Option 3: TinyLlama (Minimum Resources)**
```powershell
ollama pull tinyllama
```

**Option 4: All Models (Choose Your Favorite)**
```powershell
ollama pull phi
ollama pull mistral
ollama pull neural-chat
```

### Monitor Download Progress
```powershell
# List downloaded models
ollama list

# Check available models online
# https://ollama.ai/library
```

---

## Step 3: Test Ollama Model Locally

```powershell
# Test Phi 2 model
curl -X POST http://localhost:11434/api/generate `
  -H "Content-Type: application/json" `
  -d @- <<'EOF'
{
  "model": "phi",
  "prompt": "Tell me about rice irrigation",
  "stream": false
}
EOF
```

**Expected Response:**
```json
{
  "model": "phi",
  "created_at": "2024-12-04T10:30:45.123456Z",
  "response": "Rice irrigation is a critical agricultural practice...",
  "done": true,
  "total_duration": 2500000000,
  "load_duration": 500000000,
  "prompt_eval_count": 8,
  "eval_count": 120,
  "eval_duration": 2000000000
}
```

---

## Step 4: Integrate Ollama with AgriSense Backend

### Update requirements.txt
```bash
# Add to agrisense_app/backend/requirements.txt
ollama>=0.1.0
```

### Install Ollama Python Client
```powershell
cd "d:\AGRISENSE FULL-STACK\AGRISENSEFULL-STACK"
.\.venv\Scripts\pip install ollama
```

---

## Step 5: Update LLM Clients Module

The chatbot will now support Ollama as a local LLM option!

### New Features:
✅ **Ollama Integration**: Local LLM inference
✅ **Fallback Chain**: Ollama → Gemini → DeepSeek → Rule-based
✅ **No API Costs**: Run locally without external APIs
✅ **Configurable Model**: Choose which model to use via environment variable

### Environment Variables
```powershell
# Add to your .env file or set in terminal:
$env:OLLAMA_BASE_URL='http://localhost:11434'       # Ollama server URL
$env:OLLAMA_MODEL='phi'                             # Model to use (phi, mistral, tinyllama)
$env:OLLAMA_TIMEOUT='30'                            # Response timeout in seconds
$env:LLM_PROVIDER='ollama'                          # Set as primary LLM provider
```

---

## Step 6: Run Your AgriSense with Ollama

### Terminal 1: Start Ollama
```powershell
# Ollama usually starts automatically
# If not, run:
ollama serve
```

### Terminal 2: Start AgriSense Backend
```powershell
cd "d:\AGRISENSE FULL-STACK\AGRISENSEFULL-STACK"
.\.venv\Scripts\Activate.ps1

# Set Ollama as primary LLM
$env:OLLAMA_BASE_URL='http://localhost:11434'
$env:OLLAMA_MODEL='phi'
$env:LLM_PROVIDER='ollama'

# Run backend (with ML disabled for faster startup)
$env:AGRISENSE_DISABLE_ML='1'
python -m uvicorn agrisense_app.backend.main:app --host 0.0.0.0 --port 8004 --reload
```

### Terminal 3: Start Frontend
```powershell
cd "d:\AGRISENSE FULL-STACK\AGRISENSEFULL-STACK\agrisense_app\frontend\farm-fortune-frontend-main"
npm run dev
```

---

## Step 7: Test Chatbot with Ollama

```powershell
# Test agricultural question
$body = @{
    "question" = "How should I irrigate rice?"
} | ConvertTo-Json

$response = Invoke-WebRequest -Uri "http://localhost:8004/chatbot/ask" `
  -Method POST `
  -Body $body `
  -ContentType "application/json"

$response.Content | ConvertFrom-Json | ConvertTo-Json -Depth 10
```

**Expected Output:**
```
The chatbot now responds with Ollama-generated answers!
```

---

## API Usage Examples

### Using Ollama Directly (Python)
```python
import ollama

# Simple chat completion
response = ollama.chat(
    model='phi',
    messages=[
        {'role': 'user', 'content': 'How do I prevent rice blast disease?'}
    ],
    stream=False
)
print(response['message']['content'])
```

### Using Ollama with AgriSense Backend
```python
from agrisense_app.backend import llm_clients_ollama

# Rerank candidates using Ollama
scores = llm_clients_ollama.rerank_with_ollama(
    question="best irrigation method",
    candidates=[
        "Use drip irrigation for water efficiency",
        "Flood irrigation is traditional",
        "Sprinkler irrigation works well"
    ]
)
print(scores)  # [0.9, 0.3, 0.6]
```

---

## Troubleshooting

### Issue 1: Ollama Connection Failed
```powershell
# Check if Ollama is running
netstat -ano | Select-String 11434

# Restart Ollama
Get-Process ollama | Stop-Process -Force
ollama serve
```

### Issue 2: Model Not Found
```powershell
# List downloaded models
ollama list

# Download missing model
ollama pull phi
```

### Issue 3: Slow Response
- **Solution 1**: Use a faster model (TinyLlama or Phi)
- **Solution 2**: Reduce `OLLAMA_TIMEOUT` and accept shorter responses
- **Solution 3**: Increase system RAM if available

### Issue 4: High Memory Usage
```powershell
# Use lightweight model
$env:OLLAMA_MODEL='tinyllama'

# Or unload model to free memory
curl http://localhost:11434/api/generate -d '{"model": "phi", "keep_alive": 0}'
```

### Issue 5: GPU Acceleration Not Working
- **Windows**: Ensure NVIDIA drivers are installed (for CUDA)
- **AMD**: Install ROCm drivers for AMD GPU support
- **Check GPU Status**: `ollama serve` shows GPU info at startup

---

## Performance Optimization Tips

### 1. Model Selection
```powershell
# Fastest: TinyLlama (637 MB, 100ms response)
ollama pull tinyllama

# Balanced: Phi (1.4 GB, 500ms response)
ollama pull phi

# Most Capable: Mistral (4 GB, 2s response)
ollama pull mistral
```

### 2. Batch Processing
```powershell
# Process multiple questions at once
# Reduces model loading overhead
```

### 3. Response Caching
```powershell
# Cache common agricultural questions
# Reduces LLM calls
```

### 4. Model Preloading
```powershell
# Warm up model on startup
# Keep model in memory with: keep_alive: 5m
```

---

## Upgrading Models

```powershell
# Pull newer version (auto-updates)
ollama pull phi

# Remove old model
ollama rm phi:old

# Use specific version tag
ollama pull phi:2.5
```

---

## Monitoring & Metrics

### Check Model Performance
```powershell
# Monitor inference time
# Look for "eval_duration" in responses

# Typical speeds:
# - TinyLlama: 50-100 ms
# - Phi: 200-500 ms
# - Mistral: 1-3 seconds
```

### Monitor Memory
```powershell
# Check task manager while running
# or use:
Get-Process ollama | Select-Object Name, PrivateMemorySize
```

---

## Production Deployment

### Docker Compose with Ollama
```yaml
version: '3.8'
services:
  ollama:
    image: ollama/ollama:latest
    ports:
      - "11434:11434"
    volumes:
      - ollama_data:/root/.ollama
    environment:
      OLLAMA_MODELS: /root/.ollama/models
    command: ollama serve

  agrisense-backend:
    build: .
    ports:
      - "8004:8004"
    environment:
      OLLAMA_BASE_URL: http://ollama:11434
      OLLAMA_MODEL: phi
    depends_on:
      - ollama
    command: python -m uvicorn agrisense_app.backend.main:app --host 0.0.0.0 --port 8004

volumes:
  ollama_data:
```

---

## Next Steps

1. ✅ Install Ollama
2. ✅ Download a lightweight model (Phi recommended)
3. ✅ Test Ollama standalone
4. ✅ Install Python client: `pip install ollama`
5. ✅ Update AgriSense backend integration
6. ✅ Start services and test chatbot
7. ✅ Monitor performance and optimize

---

## Useful Resources

- **Ollama Official**: https://ollama.ai/
- **Model Library**: https://ollama.ai/library
- **Python Client**: https://github.com/ollama/ollama-python
- **API Docs**: https://github.com/ollama/ollama/blob/main/docs/api.md

---

## Quick Reference Commands

```powershell
# Download model
ollama pull phi

# List models
ollama list

# Run model interactively
ollama run phi

# Test API
curl http://localhost:11434/api/tags

# Stop model (free memory)
curl -X POST http://localhost:11434/api/generate -d '{"model": "phi", "keep_alive": 0}'

# Check model info
ollama show phi
```

---

**Ready to go!** 🚀 Proceed to Step 1 to install Ollama.
