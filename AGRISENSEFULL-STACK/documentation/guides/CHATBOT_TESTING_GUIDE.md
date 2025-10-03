# 🧪 Conversational Chatbot Testing Guide

## Quick Start Testing (5 Minutes)

### Prerequisites
1. ✅ Backend running on `http://localhost:8004`
2. ✅ Frontend running on `http://localhost:8082`

### Start Services
```powershell
# Terminal 1 - Backend
cd "d:\AGRISENSE FULL-STACK\AGRISENSEFULL-STACK"
.venv\Scripts\Activate.ps1
python -m uvicorn agrisense_app.backend.main:app --port 8004 --reload

# Terminal 2 - Frontend
cd "d:\AGRISENSE FULL-STACK\AGRISENSEFULL-STACK\agrisense_app\frontend\farm-fortune-frontend-main"
npm run dev
```

---

## Test Suite

### Test 1: Greeting Message (All Languages)

**Purpose**: Verify warm welcome in all 5 languages

**API Test**:
```powershell
# English
curl http://localhost:8004/chatbot/greeting?language=en

# Hindi
curl "http://localhost:8004/chatbot/greeting?language=hi"

# Tamil
curl "http://localhost:8004/chatbot/greeting?language=ta"

# Telugu
curl "http://localhost:8004/chatbot/greeting?language=te"

# Kannada
curl "http://localhost:8004/chatbot/greeting?language=kn"
```

**Expected Result**:
```json
{
  "language": "en",
  "greeting": "Hello! I'm here to help with your farming questions. 😊",
  "timestamp": "2025-10-02 ..."
}
```

**UI Test**:
1. Open `http://localhost:8082/chatbot`
2. Verify greeting appears automatically
3. Change language in top nav (language selector)
4. Verify greeting updates to new language

✅ **Pass Criteria**: 
- All 5 languages show appropriate greetings
- Greeting includes emoji
- UI auto-loads greeting on page load

---

### Test 2: Problem Question (Empathy Detection)

**Purpose**: Verify empathetic response for farmer problems

**Test Questions**:
```
English: "My tomato plants are dying and leaves are turning yellow"
Hindi: "मेरे टमाटर के पौधे मर रहे हैं"
Tamil: "என் தக்காளி செடிகள் இறந்து கொண்டிருக்கின்றன"
```

**API Test**:
```powershell
$body = @{
    question = "My tomato plants are dying and leaves are turning yellow"
    session_id = "test-problem-1"
    language = "en"
    top_k = 3
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8004/chatbot/ask" `
  -Method POST `
  -ContentType "application/json" `
  -Body $body | ConvertTo-Json -Depth 5
```

**Expected Response Features**:
- ✅ Empathetic opening: "I understand that can be concerning." or similar
- ✅ Solution/advice in body
- ✅ Regional context note (🌦️ or 🗺️)
- ✅ Follow-up suggestions (💡)
- ✅ Encouraging closing: "Hope this helps!" or similar

**UI Test**:
1. Type problem question in chat input
2. Press Send
3. Observe typing indicator (3 bouncing dots)
4. Wait for response

✅ **Pass Criteria**:
- Response feels warm and supportive
- Contains all conversational elements
- Follow-up buttons appear below message
- Original answer toggle works (if enabled)

---

### Test 3: General Farming Question

**Purpose**: Verify informative response for neutral questions

**Test Questions**:
```
"What is the best time to plant rice?"
"How often should I water tomatoes?"
"Which fertilizer is best for wheat?"
```

**API Test**:
```powershell
$body = @{
    question = "What is the best time to plant rice?"
    session_id = "test-general-1"
    language = "en"
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8004/chatbot/ask" `
  -Method POST `
  -ContentType "application/json" `
  -Body $body | ConvertTo-Json -Depth 5
```

**Expected Response Features**:
- ✅ Encouraging opening: "That's a very good question!" or similar
- ✅ Clear, farmer-friendly answer
- ✅ Conversational markers: "You see,", "Well,", "Here's the thing:"
- ✅ Follow-up suggestions related to topic
- ✅ Friendly closing

✅ **Pass Criteria**:
- Response is easy to understand
- Language is natural, not robotic
- Follow-ups are relevant to the topic

---

### Test 4: Multi-Turn Conversation (Memory)

**Purpose**: Verify session-based conversation tracking

**Test Sequence**:
```powershell
# Question 1
$body1 = @{
    question = "How to plant rice?"
    session_id = "test-memory-123"
    language = "en"
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8004/chatbot/ask" -Method POST -ContentType "application/json" -Body $body1

# Question 2 (related follow-up)
$body2 = @{
    question = "What about fertilizer for rice?"
    session_id = "test-memory-123"  # Same session
    language = "en"
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8004/chatbot/ask" -Method POST -ContentType "application/json" -Body $body2

# Question 3
$body3 = @{
    question = "When should I harvest?"
    session_id = "test-memory-123"  # Same session
    language = "en"
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8004/chatbot/ask" -Method POST -ContentType "application/json" -Body $body3
```

**UI Test**:
1. Ask: "How to plant rice?"
2. Wait for response
3. Ask: "What about fertilizer?" (related question)
4. Ask: "When should I harvest?" (another related question)
5. Scroll up to see conversation history

✅ **Pass Criteria**:
- All messages appear in correct order
- Session ID shown at bottom (consistent)
- Chat scrolls to latest message automatically
- Conversation feels coherent (context-aware)

---

### Test 5: Follow-Up Suggestions

**Purpose**: Verify follow-up extraction and clickability

**Test Question**:
```
"How to control pests on tomatoes?"
```

**Expected Follow-Ups**:
- "Natural pest control methods"
- "Identifying pest damage"
- "Preventive measures"

**UI Test**:
1. Ask question
2. Wait for response with follow-ups (💡 section)
3. Click on one of the follow-up buttons
4. Verify input field populates with clicked question
5. Press Send to ask the follow-up

✅ **Pass Criteria**:
- Follow-up buttons appear as pills/badges
- Clicking a follow-up pre-fills the input
- Follow-ups are relevant to original question

---

### Test 6: Multi-Language UI

**Purpose**: Verify all UI labels translate correctly

**Languages to Test**: en, hi, ta, te, kn

**UI Test**:
1. Open `http://localhost:8082/chatbot`
2. Click language selector in top nav
3. Select each language
4. Verify translations for:
   - Page title: "Agricultural Assistant Chatbot"
   - Input placeholder: "Type your farming question..."
   - Send button: "Send" / "भेजें" / "அனுப்பு" / etc.
   - "You" and "Assistant" labels
   - Loading: "Thinking..."
   - Suggested questions label
   - Show/Hide original toggle
   - Footer text

✅ **Pass Criteria**:
- All UI text translates correctly
- No English text when in non-English mode
- Native scripts render properly (Devanagari, Tamil script, etc.)
- Emojis display correctly in all languages

---

### Test 7: Typing Indicator

**Purpose**: Verify smooth loading UX

**UI Test**:
1. Ask any question
2. Immediately observe chat area
3. Look for 3 bouncing dots while waiting
4. Verify dots disappear when response arrives

✅ **Pass Criteria**:
- Typing indicator appears immediately after Send
- 3 dots animate with staggered bounce
- Indicator disappears when response ready
- No flicker or UI jump

---

### Test 8: Show/Hide Original Answer

**Purpose**: Verify debugging feature

**UI Test**:
1. Click "Show Original" button (top right of chatbot card)
2. Ask a question
3. Wait for response
4. Expand "Original Answer" details under response
5. Compare original vs enhanced text
6. Click "Hide Original" button
7. Verify original answer section disappears

✅ **Pass Criteria**:
- Toggle button works
- Original answer is different from enhanced
- Original is more technical/concise
- Enhanced has empathy + follow-ups + closing

---

### Test 9: Error Handling

**Purpose**: Verify graceful degradation

**Scenarios**:

**A) Backend Down**:
```powershell
# Stop backend (Ctrl+C)
# Try asking question in UI
```
Expected: Error message displayed, no crash

**B) Invalid Question**:
```
Question: "asdjfklasdjfkl"
```
Expected: "I couldn't find an answer" message

**C) Empty Input**:
```
Question: "" (empty)
```
Expected: Send button disabled, cannot send

✅ **Pass Criteria**:
- No white screen of death
- Error messages are user-friendly
- UI remains functional after errors

---

### Test 10: Performance

**Purpose**: Verify response time acceptable

**Test**:
```powershell
# Measure response time
Measure-Command {
    $body = @{
        question = "How to plant rice?"
        session_id = "test-perf"
        language = "en"
    } | ConvertTo-Json
    
    Invoke-RestMethod -Uri "http://localhost:8004/chatbot/ask" `
      -Method POST `
      -ContentType "application/json" `
      -Body $body
}
```

✅ **Pass Criteria**:
- Response time < 2 seconds (without ML)
- Response time < 5 seconds (with ML)
- UI remains responsive during wait

---

## 🚨 Known Issues & Workarounds

### Issue 1: ML Model Loading Slow
**Symptom**: First question takes 10+ seconds  
**Workaround**: Set `AGRISENSE_DISABLE_ML=1` for testing  
**Fix**: Lazy load models, cache in memory

### Issue 2: Session Memory Overflow
**Symptom**: Memory grows unbounded  
**Workaround**: Max 100 sessions, auto-evict old ones  
**Fix**: Already implemented (OrderedDict with LRU)

### Issue 3: Translation Missing
**Symptom**: English text appears in other languages  
**Workaround**: Check if key exists in all 5 locale files  
**Fix**: Add missing keys to `src/locales/*.json`

---

## 📊 Test Results Template

### Test Run: [Date]

| Test | Status | Notes |
|------|--------|-------|
| 1. Greeting (all languages) | ⬜ | |
| 2. Problem question (empathy) | ⬜ | |
| 3. General question | ⬜ | |
| 4. Multi-turn conversation | ⬜ | |
| 5. Follow-up suggestions | ⬜ | |
| 6. Multi-language UI | ⬜ | |
| 7. Typing indicator | ⬜ | |
| 8. Show/hide original | ⬜ | |
| 9. Error handling | ⬜ | |
| 10. Performance | ⬜ | |

**Overall Status**: ⬜ Pass / ⬜ Fail  
**Issues Found**: [List any issues]  
**Next Steps**: [Action items]

---

## 🎯 Acceptance Criteria Summary

Before deploying to production, ensure:

✅ All 10 tests pass  
✅ All 5 languages work correctly  
✅ No console errors in browser DevTools  
✅ No backend errors in uvicorn logs  
✅ Response time acceptable (< 5s)  
✅ UI is smooth and responsive  
✅ Conversation feels natural and human-like  
✅ Follow-ups are relevant and helpful  
✅ Empathy is appropriate to question type  
✅ Session memory works across multiple questions  

---

## 🔄 Continuous Testing

### Automated Testing (Future)
```python
# tests/test_chatbot_conversational.py
def test_greeting_all_languages():
    for lang in ["en", "hi", "ta", "te", "kn"]:
        response = client.get(f"/chatbot/greeting?language={lang}")
        assert response.status_code == 200
        assert "greeting" in response.json()

def test_empathy_detection():
    response = client.post("/chatbot/ask", json={
        "question": "My crops are dying",
        "language": "en"
    })
    result = response.json()["results"][0]["answer"]
    assert any(phrase in result for phrase in ["concerning", "worry", "help"])

def test_follow_up_extraction():
    response = client.post("/chatbot/ask", json={
        "question": "How to control pests?",
        "language": "en"
    })
    result = response.json()["results"][0]["answer"]
    assert "💡" in result  # Follow-ups present
```

### Manual Regression Testing
Run this checklist before each release:
- [ ] Test in all 5 supported languages
- [ ] Test on mobile viewport (responsive)
- [ ] Test with backend ML enabled
- [ ] Test with backend ML disabled
- [ ] Test error scenarios
- [ ] Test long conversation (10+ messages)
- [ ] Test concurrent users (multiple sessions)

---

**Document Version**: 1.0  
**Last Updated**: October 2, 2025  
**Status**: Ready for Testing ✅
