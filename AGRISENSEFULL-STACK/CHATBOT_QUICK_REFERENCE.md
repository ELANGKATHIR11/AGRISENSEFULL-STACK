# 🌾 AgriSense Chatbot - Quick Reference Card

**Date:** December 3, 2025  
**Version:** 1.0  
**Status:** Production Ready

---

## 🚀 Quick Start

### Start Backend
```powershell
cd "AGRISENSE FULL-STACK/AGRISENSEFULL-STACK"
.\.venv\Scripts\Activate.ps1
python -m uvicorn agrisense_app.backend.main:app --port 8004 --reload
```

### Start Frontend
```powershell
cd "AGRISENSE FULL-STACK/AGRISENSEFULL-STACK/agrisense_app/frontend/farm-fortune-frontend-main"
npm run dev
```

### Access Chatbot
- **Frontend UI:** http://localhost:8082 → Chat page
- **Backend API:** http://localhost:8004/docs (Swagger UI)

---

## 📡 API Endpoints

### 1. Main Q&A Endpoint
```http
POST /chatbot/ask
Content-Type: application/json

{
  "question": "How to grow tomatoes?",
  "top_k": 3,
  "session_id": "session-1234567890",
  "language": "en"
}
```

**Response:**
```json
{
  "question": "How to grow tomatoes?",
  "results": [
    {
      "rank": 1,
      "score": 0.92,
      "answer": "Enhanced conversational response...",
      "original_answer": "Original knowledge base answer..."
    }
  ]
}
```

### 2. Greeting Endpoint
```http
GET /chatbot/greeting?language=hi
```

**Response:**
```json
{
  "language": "hi",
  "greeting": "नमस्ते! मैं आपके खेती के सवालों में मदद करने के लिए यहाँ हूँ। 😊",
  "timestamp": "2025-12-03 10:30:45"
}
```

### 3. Context-Aware Advice
```http
POST /chatbot/advice
Content-Type: application/json

{
  "query": "Is this disease serious?",
  "diagnosis_context": {
    "crop_detected": "Tomato",
    "disease_name": "Early Blight",
    "confidence": 88.3,
    "severity": "Medium"
  }
}
```

**Response:**
```json
{
  "query": "Is this disease serious?",
  "advice": "I understand your concern - seeing those brown spots...",
  "has_diagnosis_context": true,
  "advisor": "Dr. Priya Kumar (Senior Agronomist)",
  "timestamp": "2025-12-03 10:35:22"
}
```

### 4. Reload Artifacts (Admin)
```http
POST /chatbot/reload
```

### 5. Tune Parameters (Admin)
```http
POST /chatbot/tune
Content-Type: application/json

{
  "alpha": 0.7,
  "min_cos": 0.3
}
```

---

## 🌍 Supported Languages

| Code | Language | Name |
|------|----------|------|
| `en` | English  | English |
| `hi` | Hindi    | हिंदी |
| `ta` | Tamil    | தமிழ் |
| `te` | Telugu   | తెలుగు |
| `kn` | Kannada  | ಕನ್ನಡ |

---

## 🔧 Configuration

### Environment Variables
```bash
# Backend
AGRISENSE_DISABLE_ML=0              # Enable ML features
CHATBOT_TOPK_MAX=20                 # Max results to return
GOOGLE_API_KEY=your_key_here        # For AgriAdvisorBot

# CORS
ALLOWED_ORIGINS=http://localhost:8082,http://localhost:8080
```

### Runtime Tuning
- **alpha:** Dense/lexical blend (0.0-1.0, default 0.7)
- **min_cos:** Minimum cosine similarity threshold (0.0-1.0, default 0.3)

---

## 🧪 Testing Commands

### Backend Health Check
```bash
curl http://localhost:8004/health
```

### Test Chatbot Q&A
```bash
curl -X POST http://localhost:8004/chatbot/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "How to grow rice?", "language": "en"}'
```

### Test Greeting
```bash
curl "http://localhost:8004/chatbot/greeting?language=hi"
```

### Test Context-Aware Advice
```bash
curl -X POST http://localhost:8004/chatbot/advice \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What should I do?",
    "diagnosis_context": {
      "crop_detected": "Tomato",
      "disease_name": "Early Blight",
      "severity": "High"
    }
  }'
```

---

## 📁 Key Files

### Backend
- **Main API:** `agrisense_app/backend/main.py`
- **Conversational:** `agrisense_app/backend/chatbot_conversational.py`
- **AI Advisor:** `agrisense_app/backend/core/chatbot_engine.py`
- **Knowledge Base:** `agrisense_app/backend/chatbot_qa_pairs.json`

### Frontend
- **Chatbot UI:** `agrisense_app/frontend/farm-fortune-frontend-main/src/pages/Chatbot.tsx`
- **Translations:** `agrisense_app/frontend/farm-fortune-frontend-main/src/locales/*.json`

---

## 🎯 Common Use Cases

### 1. Simple Crop Query
```
User: "tomato"
Response: Full cultivation guide for tomatoes
```

### 2. Irrigation Question
```
User: "How much water for rice?"
Response: "That's a very good question!

Rice requires consistent moisture... [detailed guidance]

💡 You might also want to know:
• optimal watering schedule
• signs of overwatering

Hope this helps! 🌾"
```

### 3. Disease Follow-up
```
Context: User uploaded diseased tomato image
Query: "Will I lose my crop?"
Response: "I understand your concern... [empathetic, detailed advice with cost estimates]"
```

### 4. Multi-turn Conversation
```
Turn 1: "How to control pests?"
Response: [Pest control guidance + follow-ups]

Turn 2: Click on "organic pest control" suggestion
Response: [Detailed organic methods]
```

---

## 🐛 Troubleshooting

### Backend Won't Start
```bash
# Check if port 8004 is available
netstat -ano | findstr :8004

# Activate virtual environment
.\.venv\Scripts\Activate.ps1

# Install missing dependencies
pip install -r agrisense_app/backend/requirements.txt
```

### Frontend Won't Start
```bash
# Check if port 8082 is available
netstat -ano | findstr :8082

# Install dependencies
npm install

# Clear cache if needed
npm run build -- --clean
```

### Chatbot Returns Empty Results
```bash
# Check if artifacts are loaded
curl http://localhost:8004/chatbot/reload

# Verify knowledge base exists
ls agrisense_app/backend/chatbot_qa_pairs.json
ls agrisense_app/backend/chatbot_index.npz
```

### AgriAdvisorBot Not Available
```bash
# Set Google API key
$env:GOOGLE_API_KEY="your_api_key_here"

# Verify import
python -c "from agrisense_app.backend.core.chatbot_engine import get_chatbot_engine; print('OK')"
```

---

## 📊 Performance Tips

### Backend Optimization
1. **Enable caching:** Already enabled (100 entry LRU cache)
2. **Adjust top_k:** Use `top_k=3` for faster responses
3. **Tune alpha:** Higher alpha (0.8+) for more semantic, lower for more lexical
4. **Reload artifacts:** Only when knowledge base changes

### Frontend Optimization
1. **Session persistence:** Use localStorage to preserve session_id
2. **Lazy loading:** Messages already use React.memo
3. **Debounce input:** Consider adding input debouncing for typing indicators

---

## 🔒 Security Considerations

### API Protection
- Use `AGRISENSE_ADMIN_TOKEN` for admin endpoints
- Enable CORS only for trusted origins
- Rate limit chatbot endpoints in production

### Data Privacy
- Session IDs are not stored persistently
- Conversation history kept in memory only
- No PII collected without consent

---

## 📈 Monitoring

### Key Metrics to Track
- **Response time:** Avg, P95, P99
- **Cache hit rate:** Should be >40%
- **Error rate:** Should be <1%
- **User satisfaction:** Collect feedback after conversations

### Logging
```python
# Enable debug logging
import logging
logging.basicConfig(level=logging.DEBUG)
```

---

## 🎓 Best Practices

### For Developers
1. Always test with multiple languages
2. Use session_id for conversation continuity
3. Check original_answer for debugging
4. Handle network errors gracefully
5. Update translations when adding features

### For Content Editors
1. Keep cultivation guides concise (<2000 chars)
2. Use bullet points for readability
3. Include emojis sparingly (🌾🌱💡)
4. Maintain consistent tone across languages
5. Test responses in all supported languages

---

## 🚀 Deployment Checklist

- [ ] Set `GOOGLE_API_KEY` environment variable
- [ ] Configure `ALLOWED_ORIGINS` for production
- [ ] Verify all translations are complete
- [ ] Test all endpoints with production data
- [ ] Enable monitoring and logging
- [ ] Set up error alerting
- [ ] Configure rate limiting
- [ ] Review security headers
- [ ] Load test with expected traffic
- [ ] Document API for external consumers

---

## 📞 Support

**Documentation:**
- Full Integration Guide: `CHATBOT_INTEGRATION_COMPLETE.md`
- Project Blueprint: `PROJECT_BLUEPRINT_UPDATED.md`
- AI Agent Guidelines: `.github/copilot-instructions.md`

**Quick Help:**
```bash
# Backend health
curl http://localhost:8004/health

# Check loaded chatbot artifacts
curl http://localhost:8004/chatbot/metrics

# View API docs
open http://localhost:8004/docs
```

---

**Last Updated:** December 3, 2025  
**Maintained By:** AgriSense Development Team
