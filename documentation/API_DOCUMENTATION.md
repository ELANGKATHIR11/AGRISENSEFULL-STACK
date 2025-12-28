# AgriSense API Documentation

**Version**: 3.0  
**Last Updated**: October 14, 2025  
**Base URL**: `http://localhost:8004`  
**API Prefix**: `/api/v1` (v1 endpoints), root level for core endpoints

---

## 📚 Table of Contents

1. [Overview](#overview)
2. [Authentication](#authentication)
3. [Core Endpoints](#core-endpoints)
4. [Smart Irrigation](#smart-irrigation)
5. [Crop Recommendation](#crop-recommendation)
6. [Disease Detection](#disease-detection)
7. [Weed Management](#weed-management)
8. [Chatbot](#chatbot)
9. [Data Management](#data-management)
10. [Error Codes](#error-codes)
11. [Rate Limiting](#rate-limiting)
12. [Examples](#examples)
13. [Troubleshooting](#troubleshooting)

---

## Overview

AgriSense provides RESTful APIs for smart agriculture solutions including:
- 🌾 **Smart Irrigation**: ML-powered water management
- 🌱 **Crop Recommendation**: Soil-based crop selection
- 🦠 **Disease Detection**: Vision-based plant disease identification
- 🌿 **Weed Management**: AI-powered weed detection
- 💬 **Agricultural Chatbot**: Natural language farming advice

### API Characteristics
- **Protocol**: HTTP/HTTPS
- **Content-Type**: `application/json`
- **Response Format**: JSON
- **Character Encoding**: UTF-8 (supports Unicode)
- **Max Request Size**: 10MB (for image uploads)
- **Timeout**: 30 seconds

---

## Authentication

### Current Version (v3.0)
- **Type**: Optional token-based authentication
- **Header**: `Authorization: Bearer <token>`
- **Public Endpoints**: Most endpoints are public for development

### Production Authentication (Coming Soon)
```http
POST /api/v1/auth/login
Content-Type: application/json

{
  "username": "farmer@example.com",
  "password": "secure_password"
}
```

**Response**:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

---

## Core Endpoints

### Health Check

**Endpoint**: `GET /health`

**Description**: Check if the API is running and healthy

**Request**:
```bash
curl http://localhost:8004/health
```

**Response**:
```json
{
  "status": "healthy",
  "version": "3.0.0",
  "timestamp": "2025-10-14T10:30:00Z",
  "services": {
    "database": "ok",
    "ml_models": "ok",
    "chatbot": "ok"
  }
}
```

**Status Codes**:
- `200 OK`: Service is healthy
- `503 Service Unavailable`: Service is down

---

### Readiness Check

**Endpoint**: `GET /ready`

**Description**: Check if the API is ready to accept requests (all dependencies loaded)

**Response**:
```json
{
  "ready": true,
  "ml_models_loaded": true,
  "database_connected": true,
  "chatbot_initialized": true
}
```

**Status Codes**:
- `200 OK`: Service is ready
- `503 Service Unavailable`: Service is not ready

---

### VLM Status

**Endpoint**: `GET /api/vlm/status`

**Description**: Check Vision-Language Model status

**Response**:
```json
{
  "vlm_available": true,
  "model_type": "comprehensive_detector",
  "version": "2.0",
  "capabilities": ["disease_detection", "weed_detection"],
  "last_inference": "2025-10-14T10:25:00Z"
}
```

---

## Smart Irrigation

### Get Irrigation Recommendation

**Endpoint**: `POST /api/v1/irrigation/recommend`

**Description**: Get water management recommendations based on sensor data

**Request**:
```json
{
  "temperature": 28.5,
  "humidity": 65.0,
  "soil_moisture": 35.0,
  "soil_ph": 6.5,
  "nitrogen": 50.0,
  "phosphorus": 40.0,
  "potassium": 45.0,
  "rainfall": 100.0,
  "crop_type": "wheat",
  "field_size_hectares": 2.0
}
```

**Field Descriptions**:
| Field | Type | Required | Range | Description |
|-------|------|----------|-------|-------------|
| `temperature` | float | Yes | -10 to 50°C | Air temperature |
| `humidity` | float | Yes | 0-100% | Relative humidity |
| `soil_moisture` | float | Yes | 0-100% | Soil moisture level |
| `soil_ph` | float | No | 0-14 | Soil pH level |
| `nitrogen` | float | No | 0-100 | Nitrogen level (ppm) |
| `phosphorus` | float | No | 0-100 | Phosphorus level (ppm) |
| `potassium` | float | No | 0-100 | Potassium level (ppm) |
| `rainfall` | float | No | 0-500mm | Recent rainfall |
| `crop_type` | string | No | - | Crop being grown |
| `field_size_hectares` | float | No | >0 | Field size |

**Response**:
```json
{
  "water_liters": 1500.0,
  "irrigation_duration_minutes": 45,
  "tips": [
    "Soil moisture is low - immediate irrigation recommended",
    "Consider drip irrigation for water efficiency",
    "Monitor soil moisture every 2 hours"
  ],
  "next_check_hours": 6,
  "confidence": 0.89,
  "model_used": "ml_enhanced"
}
```

**Status Codes**:
- `200 OK`: Recommendation generated successfully
- `400 Bad Request`: Invalid sensor data
- `422 Unprocessable Entity`: Validation error
- `500 Internal Server Error`: Server error

**Example**:
```bash
curl -X POST http://localhost:8004/api/v1/irrigation/recommend \
  -H "Content-Type: application/json" \
  -d '{
    "temperature": 28.5,
    "humidity": 65.0,
    "soil_moisture": 35.0,
    "soil_ph": 6.5
  }'
```

---

### Store Sensor Reading

**Endpoint**: `POST /api/v1/sensors/reading`

**Description**: Store a sensor reading for historical tracking

**Request**:
```json
{
  "sensor_id": "field_01_sensor_01",
  "temperature": 28.5,
  "humidity": 65.0,
  "soil_moisture": 35.0,
  "timestamp": "2025-10-14T10:30:00Z"
}
```

**Response**:
```json
{
  "id": "12345",
  "stored": true,
  "timestamp": "2025-10-14T10:30:00Z"
}
```

---

### Get Historical Readings

**Endpoint**: `GET /api/v1/sensors/history`

**Description**: Retrieve historical sensor readings

**Query Parameters**:
- `sensor_id` (optional): Filter by sensor ID
- `start_date` (optional): ISO 8601 date
- `end_date` (optional): ISO 8601 date
- `limit` (optional): Max records (default: 100, max: 1000)

**Example**:
```bash
curl "http://localhost:8004/api/v1/sensors/history?sensor_id=field_01&limit=50"
```

**Response**:
```json
{
  "readings": [
    {
      "id": "12345",
      "sensor_id": "field_01_sensor_01",
      "temperature": 28.5,
      "humidity": 65.0,
      "soil_moisture": 35.0,
      "timestamp": "2025-10-14T10:30:00Z"
    }
  ],
  "count": 50,
  "has_more": true
}
```

---

## Crop Recommendation

### Get Crop Recommendations

**Endpoint**: `POST /api/v1/crop/recommend`

**Description**: Get crop recommendations based on soil analysis

**Request**:
```json
{
  "nitrogen": 60.0,
  "phosphorus": 55.0,
  "potassium": 50.0,
  "soil_ph": 6.8,
  "temperature": 25.0,
  "humidity": 70.0,
  "rainfall": 120.0,
  "location": {
    "latitude": 12.9716,
    "longitude": 77.5946
  }
}
```

**Response**:
```json
{
  "recommendations": [
    {
      "crop": "rice",
      "confidence": 0.92,
      "suitability_score": 8.5,
      "reasons": [
        "Optimal nitrogen levels for rice cultivation",
        "Soil pH within ideal range (6.5-7.0)",
        "Good rainfall conditions"
      ],
      "expected_yield": "4.5 tons/hectare",
      "cultivation_tips": [
        "Transplant seedlings at 21-25 days",
        "Maintain 5-7cm water level",
        "Apply urea in 3 splits"
      ]
    },
    {
      "crop": "wheat",
      "confidence": 0.85,
      "suitability_score": 7.8,
      "reasons": [
        "Good phosphorus levels",
        "Suitable temperature range"
      ],
      "expected_yield": "3.2 tons/hectare"
    }
  ],
  "total_crops": 2,
  "analysis_timestamp": "2025-10-14T10:30:00Z"
}
```

**Status Codes**:
- `200 OK`: Recommendations generated
- `400 Bad Request`: Invalid soil data
- `422 Unprocessable Entity`: Validation error

---

## Disease Detection

### Detect Plant Disease

**Endpoint**: `POST /api/disease/detect`

**Description**: Detect diseases in plant images using vision models

**Request**:
```json
{
  "image_base64": "iVBORw0KGgoAAAANSUhEUgAA...",
  "crop_type": "tomato",
  "location": "field_north_section_b",
  "additional_symptoms": "yellowing leaves, wilting"
}
```

**Field Descriptions**:
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `image_base64` | string | Yes | Base64 encoded image (PNG, JPEG) |
| `crop_type` | string | No | Type of crop (helps improve accuracy) |
| `location` | string | No | Field location for tracking |
| `additional_symptoms` | string | No | Text description of symptoms |

**Response**:
```json
{
  "disease_detected": "Late Blight",
  "confidence": 0.87,
  "severity": "moderate",
  "detection_confidence": 0.87,
  "model_used": "comprehensive_vlm",
  "affected_area_percentage": 25.5,
  "treatment_recommendations": {
    "severity": "moderate",
    "urgency": "high",
    "chemical_treatments": [
      {
        "product": "Copper-based fungicide",
        "application_rate": "2-3 kg/hectare",
        "frequency": "Every 7-10 days",
        "safety_period": "14 days before harvest"
      }
    ],
    "organic_alternatives": [
      {
        "method": "Neem oil spray",
        "application_rate": "5ml per liter",
        "frequency": "Every 5 days"
      }
    ],
    "cultural_practices": [
      "Remove and destroy infected leaves",
      "Improve air circulation",
      "Avoid overhead watering",
      "Crop rotation recommended"
    ],
    "prevention_tips": [
      "Use disease-resistant varieties",
      "Maintain proper plant spacing",
      "Monitor regularly for early detection"
    ]
  },
  "similar_diseases": [
    {
      "name": "Early Blight",
      "similarity": 0.65
    }
  ],
  "analysis_timestamp": "2025-10-14T10:30:00Z"
}
```

**Image Requirements**:
- **Format**: JPEG, PNG
- **Size**: Max 10MB
- **Resolution**: 512x512 to 2048x2048 recommended
- **Quality**: Clear, well-lit images
- **Focus**: Affected plant parts should be visible

**Status Codes**:
- `200 OK`: Disease detection completed
- `400 Bad Request`: Invalid image or parameters
- `413 Payload Too Large`: Image too large
- `422 Unprocessable Entity`: Image cannot be processed
- `500 Internal Server Error`: Detection failed

**Example**:
```bash
# Using base64 encoded image
IMAGE_BASE64=$(base64 -w 0 tomato_leaf.jpg)

curl -X POST http://localhost:8004/api/disease/detect \
  -H "Content-Type: application/json" \
  -d "{
    \"image_base64\": \"$IMAGE_BASE64\",
    \"crop_type\": \"tomato\"
  }"
```

---

## Weed Management

### Analyze Field for Weeds

**Endpoint**: `POST /api/weed/analyze`

**Description**: Analyze field images for weed detection and management recommendations

**Request**:
```json
{
  "image_base64": "iVBORw0KGgoAAAANSUhEUgAA...",
  "field_size_hectares": 2.0,
  "crop_type": "wheat",
  "growth_stage": "vegetative"
}
```

**Response**:
```json
{
  "weed_coverage_percentage": 15.5,
  "weed_density": "moderate",
  "weed_types_detected": [
    {
      "type": "broadleaf",
      "percentage": 60.0,
      "confidence": 0.82
    },
    {
      "type": "grass",
      "percentage": 40.0,
      "confidence": 0.75
    }
  ],
  "recommended_action": "selective_herbicide",
  "urgency": "medium",
  "treatment_recommendations": {
    "chemical_options": [
      {
        "herbicide": "2,4-D",
        "application_rate": "1.5 L/hectare",
        "timing": "Post-emergence",
        "target_weeds": ["broadleaf"],
        "cost_estimate": "$45/hectare"
      }
    ],
    "mechanical_options": [
      {
        "method": "Inter-row cultivation",
        "timing": "Early morning",
        "frequency": "Every 2 weeks",
        "cost_estimate": "$30/hectare"
      }
    ],
    "cultural_practices": [
      "Increase seeding rate to suppress weeds",
      "Use mulch in critical areas",
      "Consider cover crops in off-season"
    ]
  },
  "economic_impact": {
    "potential_yield_loss": "12-18%",
    "treatment_cost": "$45-75/hectare",
    "cost_benefit_ratio": 3.2
  },
  "model_used": "weed_vlm",
  "analysis_timestamp": "2025-10-14T10:30:00Z"
}
```

**Status Codes**:
- `200 OK`: Analysis completed
- `400 Bad Request`: Invalid image or parameters
- `413 Payload Too Large`: Image too large
- `500 Internal Server Error`: Analysis failed

---

## Chatbot

### Ask Agriculture Question

**Endpoint**: `POST /chatbot/ask`

**Description**: Get farming advice and cultivation guides through natural language

**Request**:
```json
{
  "question": "How do I grow carrots?",
  "language": "en",
  "context": {
    "location": "Karnataka, India",
    "season": "winter"
  }
}
```

**Supported Languages**:
- `en`: English
- `hi`: Hindi (हिंदी)
- `ta`: Tamil (தமிழ்)
- `te`: Telugu (తెలుగు)
- `kn`: Kannada (ಕನ್ನಡ)

**Response**:
```json
{
  "results": [
    {
      "answer": "**Carrot Cultivation Guide**\n\n**Climate Requirements:**\nCarrots grow best in cool weather with temperatures between 15-20°C...\n\n**Soil Preparation:**\n1. Use well-drained, sandy loam soil\n2. pH should be 6.0-6.8\n3. Add organic compost...",
      "confidence": 0.92,
      "source": "cultivation_guide",
      "related_topics": ["soil_preparation", "irrigation", "pest_management"]
    }
  ],
  "conversation_id": "conv_12345",
  "timestamp": "2025-10-14T10:30:00Z"
}
```

**Special Queries**:
- **Crop names** (e.g., "carrot", "tomato"): Returns full cultivation guide
- **Farming practices** (e.g., "organic farming"): Returns best practices
- **Pest management** (e.g., "aphids control"): Returns treatment options
- **General questions**: Returns relevant agricultural advice

**Unicode Support**:
The chatbot fully supports Unicode characters for multi-language queries:

```bash
# Hindi query example
curl -X POST http://localhost:8004/chatbot/ask \
  -H "Content-Type: application/json; charset=utf-8" \
  -d '{
    "question": "गाजर कैसे उगाएं?",
    "language": "hi"
  }'
```

**Status Codes**:
- `200 OK`: Question answered
- `400 Bad Request`: Invalid question format
- `429 Too Many Requests`: Rate limit exceeded

---

## Data Management

### Export Data

**Endpoint**: `GET /api/v1/data/export`

**Description**: Export sensor data and recommendations

**Query Parameters**:
- `format`: `json`, `csv`, `excel`
- `start_date`: ISO 8601 date
- `end_date`: ISO 8601 date
- `data_type`: `sensors`, `recommendations`, `all`

**Example**:
```bash
curl "http://localhost:8004/api/v1/data/export?format=csv&data_type=sensors" \
  -o sensor_data.csv
```

**Response**: File download (CSV/JSON/Excel)

---

### Clear Historical Data

**Endpoint**: `DELETE /api/v1/data/clear`

**Description**: Clear historical data (admin only)

**Request**:
```json
{
  "data_type": "sensors",
  "before_date": "2025-01-01T00:00:00Z",
  "confirm": true
}
```

**Response**:
```json
{
  "deleted": true,
  "records_removed": 1500,
  "data_type": "sensors"
}
```

---

## Error Codes

### Standard Error Response Format

```json
{
  "error": true,
  "code": "VALIDATION_ERROR",
  "message": "Invalid sensor data: temperature out of range",
  "details": {
    "field": "temperature",
    "value": 150,
    "expected_range": "-10 to 50"
  },
  "timestamp": "2025-10-14T10:30:00Z",
  "request_id": "req_12345"
}
```

### Error Codes Reference

| Code | HTTP Status | Description | Resolution |
|------|-------------|-------------|------------|
| `VALIDATION_ERROR` | 400 | Invalid input data | Check request parameters |
| `AUTHENTICATION_FAILED` | 401 | Invalid credentials | Verify auth token |
| `PERMISSION_DENIED` | 403 | Insufficient permissions | Check user role |
| `NOT_FOUND` | 404 | Resource not found | Verify endpoint URL |
| `METHOD_NOT_ALLOWED` | 405 | Wrong HTTP method | Use correct method (GET/POST) |
| `PAYLOAD_TOO_LARGE` | 413 | Request too large | Reduce image size |
| `RATE_LIMIT_EXCEEDED` | 429 | Too many requests | Wait and retry |
| `INTERNAL_ERROR` | 500 | Server error | Contact support |
| `SERVICE_UNAVAILABLE` | 503 | Service down | Try again later |

---

## Rate Limiting

### Current Limits (Development)
- **General Endpoints**: 100 requests/minute
- **Image Analysis**: 20 requests/minute
- **Chatbot**: 30 requests/minute

### Production Limits
- **Free Tier**: 1,000 requests/day
- **Premium Tier**: 10,000 requests/day
- **Enterprise**: Unlimited

### Rate Limit Headers
```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1697280000
```

### Rate Limit Exceeded Response
```json
{
  "error": true,
  "code": "RATE_LIMIT_EXCEEDED",
  "message": "Rate limit exceeded. Please try again in 42 seconds.",
  "retry_after": 42
}
```

---

## Examples

### Complete Workflow Example

```python
import requests
import base64
import json

BASE_URL = "http://localhost:8004"

# 1. Check API health
health = requests.get(f"{BASE_URL}/health")
print(f"API Status: {health.json()['status']}")

# 2. Get irrigation recommendation
sensor_data = {
    "temperature": 28.5,
    "humidity": 65.0,
    "soil_moisture": 35.0,
    "soil_ph": 6.5
}
irrigation = requests.post(
    f"{BASE_URL}/api/v1/irrigation/recommend",
    json=sensor_data
)
print(f"Water needed: {irrigation.json()['water_liters']} liters")

# 3. Detect plant disease
with open("plant_image.jpg", "rb") as image_file:
    image_base64 = base64.b64encode(image_file.read()).decode()

disease_response = requests.post(
    f"{BASE_URL}/api/disease/detect",
    json={
        "image_base64": image_base64,
        "crop_type": "tomato"
    }
)
disease = disease_response.json()
print(f"Disease: {disease.get('disease_detected', 'None')}")
print(f"Severity: {disease.get('severity', 'Unknown')}")

# 4. Ask chatbot for advice
chatbot_response = requests.post(
    f"{BASE_URL}/chatbot/ask",
    json={"question": "How to prevent tomato blight?"}
)
print(f"Advice: {chatbot_response.json()['results'][0]['answer'][:200]}...")
```

### JavaScript/TypeScript Example

```typescript
const BASE_URL = 'http://localhost:8004';

// Get irrigation recommendation
async function getIrrigationRecommendation() {
  const response = await fetch(`${BASE_URL}/api/v1/irrigation/recommend`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      temperature: 28.5,
      humidity: 65.0,
      soil_moisture: 35.0,
      soil_ph: 6.5
    })
  });
  
  const data = await response.json();
  console.log(`Water needed: ${data.water_liters} liters`);
  return data;
}

// Detect disease from image
async function detectDisease(imageFile: File) {
  const reader = new FileReader();
  
  return new Promise((resolve, reject) => {
    reader.onload = async () => {
      const base64 = reader.result.split(',')[1];
      
      const response = await fetch(`${BASE_URL}/api/disease/detect`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          image_base64: base64,
          crop_type: 'tomato'
        })
      });
      
      const data = await response.json();
      resolve(data);
    };
    
    reader.onerror = reject;
    reader.readAsDataURL(imageFile);
  });
}
```

---

## Troubleshooting

### Common Issues & Solutions

#### 1. Connection Refused
**Symptom**: `Connection refused` or `ECONNREFUSED`

**Causes**:
- Backend server not running
- Wrong port number
- Firewall blocking connection

**Solutions**:
```bash
# Check if backend is running
curl http://localhost:8004/health

# Start backend if not running
cd AGRISENSEFULL-STACK
.\.venv\Scripts\Activate.ps1
python -m uvicorn agrisense_app.backend.main:app --port 8004

# Check if port is in use
netstat -ano | findstr :8004
```

#### 2. Image Upload Fails
**Symptom**: `413 Payload Too Large` or `422 Unprocessable Entity`

**Causes**:
- Image too large (>10MB)
- Invalid base64 encoding
- Wrong image format

**Solutions**:
```python
# Resize image before upload
from PIL import Image
import io
import base64

def resize_and_encode(image_path, max_size=(1024, 1024)):
    img = Image.open(image_path)
    img.thumbnail(max_size, Image.Resampling.LANCZOS)
    
    buffer = io.BytesIO()
    img.save(buffer, format='JPEG', quality=85)
    return base64.b64encode(buffer.getvalue()).decode()

# Use the resized image
image_base64 = resize_and_encode("large_image.jpg")
```

#### 3. Chatbot Returns Short Answers
**Symptom**: Chatbot returns just crop name instead of full guide

**Causes**:
- Chatbot artifacts not loaded
- Function using wrong data source

**Solutions**:
```bash
# Reload chatbot artifacts
cd AGRISENSEFULL-STACK
python scripts/reload_chatbot.py

# Restart backend
# Stop current process, then:
python -m uvicorn agrisense_app.backend.main:app --port 8004
```

#### 4. Unicode/Encoding Errors
**Symptom**: `UnicodeDecodeError` or garbled text in responses

**Causes**:
- Missing UTF-8 encoding
- Windows console encoding issues

**Solutions**:
```python
# Python: Always use UTF-8
import sys
import io

# Set UTF-8 for stdout
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# PowerShell: Set console encoding
$OutputEncoding = [console]::InputEncoding = [console]::OutputEncoding = [System.Text.UTF8Encoding]::new()
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

# Requests: Specify encoding
response = requests.post(url, json=data)
response.encoding = 'utf-8'
text = response.text
```

#### 5. ML Models Not Loading
**Symptom**: `model_used: "rule_based"` instead of `"ml_enhanced"`

**Causes**:
- ML dependencies not installed
- `AGRISENSE_DISABLE_ML=1` environment variable set
- Model files missing

**Solutions**:
```bash
# Check ML status
curl http://localhost:8004/api/vlm/status

# Install ML dependencies
pip install -r agrisense_app/backend/requirements.txt

# Enable ML models
$env:AGRISENSE_DISABLE_ML='0'

# Restart backend
python -m uvicorn agrisense_app.backend.main:app --port 8004
```

#### 6. CORS Errors
**Symptom**: `CORS policy blocked` in browser console

**Causes**:
- Frontend origin not in allowed origins
- Missing CORS headers

**Solutions**:
Check `agrisense_app/backend/main.py`:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:8080",
        "http://localhost:8082"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

#### 7. Rate Limit Exceeded
**Symptom**: `429 Too Many Requests`

**Solutions**:
```python
# Implement exponential backoff
import time

def make_request_with_retry(url, data, max_retries=3):
    for i in range(max_retries):
        response = requests.post(url, json=data)
        
        if response.status_code == 429:
            retry_after = int(response.headers.get('Retry-After', 2 ** i))
            print(f"Rate limited. Waiting {retry_after}s...")
            time.sleep(retry_after)
            continue
        
        return response
    
    raise Exception("Max retries exceeded")
```

#### 8. Slow Response Times
**Symptom**: Requests taking >10 seconds

**Causes**:
- Large images
- ML model inference
- Database queries

**Solutions**:
```bash
# Check endpoint performance
curl -w "@curl-format.txt" -o /dev/null -s http://localhost:8004/health

# curl-format.txt:
time_namelookup:  %{time_namelookup}\n
time_connect:  %{time_connect}\n
time_starttransfer:  %{time_starttransfer}\n
time_total:  %{time_total}\n

# Optimize images
# Use smaller images (512x512 instead of 4000x3000)
# Use JPEG instead of PNG
# Enable async processing for long operations
```

### Getting Help

**Documentation**:
- API Docs: This file
- User Guide: `documentation/user/FARMER_GUIDE.md`
- Developer Guide: `.github/copilot-instructions.md`

**Support**:
- GitHub Issues: [Report bugs](https://github.com/your-repo/issues)
- Email: support@agrisense.example
- Community: [Forum](https://forum.agrisense.example)

**Diagnostics**:
```bash
# Run comprehensive diagnostics
python scripts/diagnose_api.py

# Check logs
Get-Content agrisense_app/backend/uvicorn.log -Tail 100

# Test all endpoints
python scripts/test_backend_integration.py
```

---

## API Versioning

### Current Version: v3.0
- Released: October 14, 2025
- Status: Stable

### Version History
- **v3.0** (Oct 2025): Added VLM models, improved disease detection
- **v2.0** (Sep 2025): Added multi-language chatbot, 48 crops
- **v1.0** (Aug 2025): Initial release with basic features

### Deprecation Policy
- Versions supported for 12 months after new release
- Breaking changes only in major versions
- Deprecation warnings 6 months before removal

---

**Last Updated**: October 14, 2025  
**Maintained By**: AgriSense Development Team  
**Version**: 3.0.0
