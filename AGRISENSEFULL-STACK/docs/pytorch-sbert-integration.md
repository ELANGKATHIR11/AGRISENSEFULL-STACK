# PyTorch SentenceTransformer Integration

This implementation adds support for loading PyTorch SentenceTransformer models directly at runtime instead of requiring TensorFlow SavedModel conversion.

## Features

- **Runtime Loading**: Load SentenceTransformer models directly using PyTorch
- **Fallback Support**: Gracefully falls back to TensorFlow SavedModel if PyTorch is unavailable
- **Environment Control**: Configure behavior using environment variables
- **Backward Compatibility**: Maintains same API interface as existing TFSMLayer implementation

## Environment Variables

### AGRISENSE_USE_PYTORCH_SBERT
Controls whether to use PyTorch SentenceTransformer:
- `1`, `true`, `yes`: Force PyTorch usage
- `auto` (default): Try PyTorch first, fallback to TensorFlow
- `0`, `false`, `no`: Skip PyTorch, use TensorFlow only

### AGRISENSE_SBERT_MODEL  
Specifies the SentenceTransformer model to load:
- Default: `sentence-transformers/all-MiniLM-L6-v2`
- Example: `sentence-transformers/paraphrase-MiniLM-L6-v2`

## Usage Examples

### Force PyTorch Usage
```bash
export AGRISENSE_USE_PYTORCH_SBERT=1
export AGRISENSE_SBERT_MODEL=sentence-transformers/all-MiniLM-L6-v2
uvicorn agrisense_app.backend.main:app
```

### Auto-detection (Default)
```bash
# Will try PyTorch first, fallback to TensorFlow SavedModel if needed
uvicorn agrisense_app.backend.main:app
```

### Force TensorFlow Only
```bash
export AGRISENSE_USE_PYTORCH_SBERT=0
uvicorn agrisense_app.backend.main:app
```

## Implementation Details

### PyTorchSentenceEncoder Class
- Provides TFSMLayer-compatible interface
- Handles both TensorFlow tensor and string list inputs
- L2-normalizes embeddings for cosine similarity
- Graceful error handling for missing dependencies

### Loading Logic
1. Check `AGRISENSE_USE_PYTORCH_SBERT` environment variable
2. If PyTorch requested/auto, try to load SentenceTransformer model
3. On success, use PyTorch backend for embeddings
4. On failure, fallback to TensorFlow SavedModel (if available)
5. Log appropriate messages for debugging

### Error Handling
- Missing PyTorch/sentence-transformers dependencies
- Model download failures  
- Runtime encoding errors
- Maintains system stability with graceful fallbacks

## Benefits

1. **Simplified Pipeline**: No need for TensorFlow conversion step
2. **Model Flexibility**: Easy to change models via environment variable
3. **Development Speed**: Faster iteration without conversion artifacts
4. **Resource Efficiency**: Direct PyTorch inference can be more efficient
5. **Latest Models**: Access to newest SentenceTransformer models without conversion

## Testing

Test the PyTorch integration:
```bash
# Test with PyTorch backend
AGRISENSE_USE_PYTORCH_SBERT=1 python -c "
import requests
response = requests.get('http://localhost:8004/chatbot/ask?question=test')
print(response.json())
"
```

Check server logs to see which backend was loaded:
- "Using PyTorch SentenceTransformer: ..." = PyTorch backend
- "Using TensorFlow SavedModel for chatbot embeddings" = TensorFlow backend