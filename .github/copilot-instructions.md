# GitHub Copilot Instructions for AgriSense Project

## Project Overview
AgriSense is a full-stack agricultural IoT platform that combines:
- **Backend**: FastAPI (Python 3.12.10) with ML/AI capabilities
- **Frontend**: React + Vite with TypeScript
- **IoT**: ESP32 & Arduino sensors for agricultural monitoring
- **AI/ML**: PyTorch, Transformers, Computer Vision for crop analysis
- **Database**: SQLite (dev) → Azure Cosmos DB (production)
- **Deployment**: Azure Container Apps, Azure services

## Core Technologies
- **Python**: 3.12.10 with async/await patterns
- **FastAPI**: RESTful API with OpenAPI docs
- **React**: 18.3+ with hooks and modern patterns
- **TypeScript**: Strict mode enabled
- **Azure**: Cosmos DB, Container Apps, OpenAI services

---

## 🐛 Debugging Guidelines

### Python Backend Debugging
```python
# Always use structured logging
import logging
logger = logging.getLogger(__name__)

# Include context in error messages
try:
    result = await process_sensor_data(device_id, data)
except Exception as e:
    logger.error(f"Failed to process sensor data for device {device_id}: {e}", exc_info=True)
    raise
```

**Best Practices:**
1. Use `logger.debug()` for detailed trace information
2. Use `logger.info()` for business logic flow
3. Use `logger.error()` with `exc_info=True` for exceptions
4. Include device_id, user_id, or request_id in logs for traceability
5. Use FastAPI's dependency injection for testable code

### Frontend Debugging
```typescript
// Use console groups for complex operations
console.group('Sensor Data Processing');
console.log('Device ID:', deviceId);
console.log('Raw data:', rawData);
console.groupEnd();

// Add error boundaries for React components
// Use React Query for API state management
```

**Best Practices:**
1. Use React DevTools for component inspection
2. Implement error boundaries for graceful degradation
3. Use TypeScript strict mode to catch type errors early
4. Add data validation at API boundaries

### Common Issues to Check
- **CORS errors**: Verify backend CORS middleware configuration
- **Authentication**: Check JWT token expiration and refresh logic
- **Database**: Ensure proper connection pooling and transaction handling
- **Memory leaks**: Monitor long-running processes with `psutil`
- **Rate limiting**: Check `slowapi` configuration for API throttling

---

## 🚀 Enhancement Strategies

### Adding New Features

#### 1. New API Endpoint
```python
# agrisense_app/backend/api/routes/new_feature.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from ..dependencies import get_current_user, get_db

router = APIRouter(prefix="/api/v1/new-feature", tags=["new-feature"])

@router.post("/")
async def create_feature(
    data: FeatureCreate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Create new feature with proper validation and error handling.
    
    - Validates input data
    - Checks user permissions
    - Returns structured response
    """
    # Implementation
    pass
```

**Checklist:**
- [ ] Add Pydantic models for request/response validation
- [ ] Implement proper error handling with HTTP status codes
- [ ] Add authentication/authorization checks
- [ ] Write unit tests (pytest)
- [ ] Add integration tests (pytest-asyncio)
- [ ] Update OpenAPI documentation
- [ ] Add rate limiting if needed

#### 2. New Frontend Component
```typescript
// agrisense_app/frontend/farm-fortune-frontend-main/src/components/NewFeature.tsx
import { FC, useState, useEffect } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import { apiClient } from '@/lib/api';

interface NewFeatureProps {
  deviceId: string;
}

export const NewFeature: FC<NewFeatureProps> = ({ deviceId }) => {
  // Use React Query for data fetching
  const { data, isLoading, error } = useQuery({
    queryKey: ['feature', deviceId],
    queryFn: () => apiClient.get(`/api/v1/feature/${deviceId}`)
  });

  if (isLoading) return <LoadingSpinner />;
  if (error) return <ErrorMessage error={error} />;
  
  return <div>{/* Component JSX */}</div>;
};
```

**Checklist:**
- [ ] Use TypeScript for type safety
- [ ] Implement proper loading/error states
- [ ] Add accessibility attributes (ARIA)
- [ ] Write component tests (Vitest/Testing Library)
- [ ] Add responsive design (mobile-first)
- [ ] Integrate with existing UI component library

### AI/ML Enhancements

#### Adding New ML Models
```python
# agrisense_app/backend/services/ml/new_model.py
import torch
from transformers import AutoModel, AutoTokenizer
from pathlib import Path

class NewMLModel:
    def __init__(self, model_path: Path):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model = AutoModel.from_pretrained(model_path).to(self.device)
        self.tokenizer = AutoTokenizer.from_pretrained(model_path)
    
    async def predict(self, input_data: dict) -> dict:
        """
        Make predictions with proper error handling.
        
        Returns:
            dict: Prediction results with confidence scores
        """
        with torch.no_grad():
            # Implementation
            pass
```

**Best Practices:**
1. Load models once at startup, reuse across requests
2. Use GPU if available (`torch.cuda.is_available()`)
3. Implement batching for multiple predictions
4. Add model versioning for reproducibility
5. Monitor inference time and memory usage
6. Cache predictions when appropriate

---

## ⚡ Optimization Strategies

### Backend Performance

#### Database Optimization
```python
# Use async SQLAlchemy properly
from sqlalchemy import select
from sqlalchemy.orm import selectinload

# Eager load relationships to avoid N+1 queries
async def get_device_with_readings(db: AsyncSession, device_id: str):
    result = await db.execute(
        select(Device)
        .options(selectinload(Device.sensor_readings))
        .where(Device.id == device_id)
    )
    return result.scalar_one_or_none()

# Use indexes for frequently queried fields
# Add to models:
# __table_args__ = (Index('idx_device_timestamp', 'device_id', 'timestamp'),)
```

#### API Optimization
```python
# Use background tasks for non-blocking operations
from fastapi import BackgroundTasks

@router.post("/process")
async def process_data(
    data: DataInput,
    background_tasks: BackgroundTasks
):
    # Immediate response
    background_tasks.add_task(heavy_processing, data)
    return {"status": "processing", "task_id": task_id}

# Implement caching with Redis or in-memory cache
from functools import lru_cache

@lru_cache(maxsize=128)
def get_model_config(model_name: str) -> dict:
    # Expensive operation cached
    return load_config(model_name)
```

#### ML Model Optimization
```python
# Use torch.jit for model optimization
import torch

# Compile model for faster inference
model = torch.jit.script(model)

# Use mixed precision for GPU
from torch.cuda.amp import autocast

with autocast():
    output = model(input_tensor)
```

### Frontend Performance

#### React Optimization
```typescript
// Use React.memo for expensive components
export const ExpensiveComponent = React.memo(({ data }) => {
  // Component logic
}, (prevProps, nextProps) => {
  // Custom comparison
  return prevProps.data.id === nextProps.data.id;
});

// Use useMemo for expensive calculations
const processedData = useMemo(() => {
  return expensiveOperation(rawData);
}, [rawData]);

// Use useCallback for event handlers
const handleClick = useCallback(() => {
  // Handler logic
}, [dependency]);
```

#### Code Splitting
```typescript
// Lazy load routes
import { lazy, Suspense } from 'react';

const Dashboard = lazy(() => import('@/pages/Dashboard'));
const Analytics = lazy(() => import('@/pages/Analytics'));

// In router
<Route 
  path="/dashboard" 
  element={
    <Suspense fallback={<LoadingSpinner />}>
      <Dashboard />
    </Suspense>
  } 
/>
```

---

## 🧪 Testing Requirements

### Backend Testing
```python
# pytest with async support
import pytest
from httpx import AsyncClient
from app.main import app

@pytest.mark.asyncio
async def test_create_sensor_reading(async_client: AsyncClient):
    """Test sensor reading creation with proper validation."""
    response = await async_client.post(
        "/api/v1/sensors/readings",
        json={
            "device_id": "TEST_001",
            "temperature": 25.5,
            "humidity": 60.0
        },
        headers={"Authorization": f"Bearer {test_token}"}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["device_id"] == "TEST_001"
    assert "id" in data
```

**Testing Checklist:**
- [ ] Unit tests for business logic (>80% coverage)
- [ ] Integration tests for API endpoints
- [ ] Database tests with test fixtures
- [ ] Mock external services (OpenAI, Azure)
- [ ] Test authentication/authorization flows
- [ ] Load testing with Locust

### Frontend Testing
```typescript
// Vitest + Testing Library
import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

describe('SensorCard', () => {
  it('displays sensor data correctly', () => {
    const queryClient = new QueryClient();
    
    render(
      <QueryClientProvider client={queryClient}>
        <SensorCard deviceId="TEST_001" />
      </QueryClientProvider>
    );
    
    expect(screen.getByText('Temperature')).toBeInTheDocument();
  });
});
```

---

## 📝 Code Quality Standards

### Python Style Guide
```python
# Follow PEP 8 and use type hints
from typing import Optional, List
from datetime import datetime

async def process_sensor_data(
    device_id: str,
    readings: List[dict],
    timestamp: Optional[datetime] = None
) -> dict:
    """
    Process sensor readings with validation.
    
    Args:
        device_id: Unique device identifier
        readings: List of sensor readings
        timestamp: Optional timestamp, defaults to now
        
    Returns:
        dict: Processed data with metadata
        
    Raises:
        ValueError: If readings are invalid
        DeviceNotFoundError: If device doesn't exist
    """
    if not readings:
        raise ValueError("Readings list cannot be empty")
    
    # Implementation
    return {"status": "success", "data": processed_data}
```

**Code Quality Tools:**
- `black` for formatting (line length: 100)
- `isort` for import sorting
- `mypy` for type checking
- `pylint` for linting (score > 9.0)
- `pytest-cov` for coverage (> 80%)

### TypeScript Style Guide
```typescript
// Use explicit types, avoid 'any'
interface SensorReading {
  id: string;
  deviceId: string;
  temperature: number;
  humidity: number;
  timestamp: Date;
}

// Use async/await over promises
async function fetchSensorData(deviceId: string): Promise<SensorReading[]> {
  try {
    const response = await apiClient.get<SensorReading[]>(`/sensors/${deviceId}`);
    return response.data;
  } catch (error) {
    logger.error('Failed to fetch sensor data', { deviceId, error });
    throw error;
  }
}

// Use const assertions for constants
export const SENSOR_TYPES = ['temperature', 'humidity', 'soil'] as const;
export type SensorType = typeof SENSOR_TYPES[number];
```

---

## 🌍 Azure Cosmos DB Integration

### Best Practices for Cosmos DB Migration

```python
# Use hierarchical partition keys for scalability
from azure.cosmos import CosmosClient, PartitionKey

container = database.create_container_if_not_exists(
    id="SensorData",
    partition_key=PartitionKey(path="/deviceId"),
    default_ttl=7776000  # 90 days TTL
)

# Efficient querying
query = "SELECT * FROM c WHERE c.deviceId = @deviceId AND c.timestamp >= @start"
parameters = [
    {"name": "@deviceId", "value": device_id},
    {"name": "@start", "value": start_time.isoformat()}
]

items = list(container.query_items(
    query=query,
    parameters=parameters,
    enable_cross_partition_query=False  # Single partition query
))
```

**Cosmos DB Optimization:**
1. Use partition keys that match query patterns (`deviceId`, `fieldId`)
2. Implement TTL for automatic data cleanup
3. Use bulk operations for batch inserts
4. Monitor RU consumption and scale accordingly
5. Implement retry logic with exponential backoff
6. Use indexing policies to exclude unnecessary fields

---

## 🔧 Environment-Specific Configuration

### Development
```python
# config/development.py
DEBUG = True
LOG_LEVEL = "DEBUG"
DATABASE_URL = "sqlite+aiosqlite:///./sensors.db"
CORS_ORIGINS = ["http://localhost:5173", "http://localhost:3000"]
```

### Production
```python
# config/production.py
DEBUG = False
LOG_LEVEL = "INFO"
DATABASE_URL = os.getenv("COSMOS_CONNECTION_STRING")
CORS_ORIGINS = [os.getenv("FRONTEND_URL")]
ENABLE_METRICS = True
SENTRY_DSN = os.getenv("SENTRY_DSN")
```

---

## 🚦 Deployment Checklist

### Pre-Deployment
- [ ] Run all tests: `pytest tests/ -v --cov`
- [ ] Check code quality: `pylint agrisense_app/backend/`
- [ ] Verify type hints: `mypy agrisense_app/backend/`
- [ ] Build frontend: `npm run build --mode production`
- [ ] Update dependencies: Check for security vulnerabilities
- [ ] Review environment variables in Azure
- [ ] Test database migrations

### Post-Deployment
- [ ] Monitor logs in Azure Application Insights
- [ ] Check API health endpoint: `/health`
- [ ] Verify frontend loads correctly
- [ ] Test critical user flows (login, data submission)
- [ ] Monitor RU consumption in Cosmos DB
- [ ] Set up alerts for errors/performance issues

---

## 📊 Monitoring and Observability

### Metrics to Track
```python
# Use prometheus_client for metrics
from prometheus_client import Counter, Histogram

request_count = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

request_duration = Histogram(
    'http_request_duration_seconds',
    'HTTP request latency',
    ['method', 'endpoint']
)
```

**Key Metrics:**
- API response times (p50, p95, p99)
- Error rates by endpoint
- Database query performance
- ML model inference time
- Memory and CPU usage
- Active WebSocket connections
- IoT device connectivity status

---

## 🔐 Security Best Practices

### Authentication
```python
# Use proper JWT validation
from fastapi.security import HTTPBearer
from jose import jwt, JWTError

security = HTTPBearer()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(
            credentials.credentials,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401)
        return user_id
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
```

**Security Checklist:**
- [ ] Use environment variables for secrets (never commit)
- [ ] Implement rate limiting on sensitive endpoints
- [ ] Validate all user inputs with Pydantic
- [ ] Use HTTPS in production (enforce with middleware)
- [ ] Implement proper CORS policies
- [ ] Hash passwords with bcrypt/argon2
- [ ] Use Azure Key Vault for production secrets
- [ ] Regular security audits with `safety` and `pip-audit`

---

## 🎯 Future Enhancement Ideas

### High Priority
1. **Real-time Data Streaming**: Implement WebSocket for live sensor updates
2. **Advanced Analytics**: Time-series analysis with Prophet or LSTM models
3. **Mobile App**: React Native app for field technicians
4. **Alerting System**: SMS/email alerts for critical sensor thresholds
5. **Data Export**: PDF reports and CSV downloads

### Medium Priority
1. **Multi-tenancy**: Support for multiple farms/organizations
2. **Geospatial Analysis**: Integration with mapping services
3. **Weather Integration**: Combine with weather API data
4. **Predictive Maintenance**: ML models for equipment failure prediction
5. **Offline Support**: PWA with offline-first capabilities

### Low Priority
1. **Voice Commands**: Integration with Alexa/Google Assistant
2. **Drone Integration**: Aerial imagery analysis
3. **Blockchain**: Immutable crop history records
4. **AR Visualization**: Augmented reality field views

---

## 📚 Additional Resources

### Documentation
- FastAPI: https://fastapi.tiangolo.com/
- React: https://react.dev/
- Azure Cosmos DB: https://learn.microsoft.com/azure/cosmos-db/
- PyTorch: https://pytorch.org/docs/
- Transformers: https://huggingface.co/docs/transformers/

### AgriSense-Specific Docs
- Architecture Diagram: `ARCHITECTURE_DIAGRAM.md` (root directory)
- Azure Deployment Guide: `AZURE_DEPLOYMENT_QUICKSTART.md` (root directory)
- Production Deployment: `PRODUCTION_DEPLOYMENT_GUIDE.md` (root directory)
- Documentation Index: `DOCUMENTATION_INDEX.md` (root directory)

---

## 💡 When Working on This Project

### Always Remember:
1. **Context First**: Understand the agricultural IoT context
2. **Data Quality**: Sensor data quality is critical for ML predictions
3. **Scalability**: Design for multiple farms and thousands of sensors
4. **Reliability**: Farmers depend on accurate, timely data
5. **User Experience**: Keep UI simple for non-technical users
6. **Cost Optimization**: Monitor Azure costs (RUs, compute, storage)
7. **Documentation**: Keep README and API docs updated

### Before Making Changes:
1. Read relevant documentation in `/documentation/` folder
2. Check existing patterns in codebase
3. Run tests locally before committing
4. Update tests for new features
5. Consider backward compatibility
6. Think about Azure Cosmos DB implications

### Code Review Focus:
- Error handling completeness
- Type safety and validation
- Performance implications
- Security considerations
- Test coverage
- Documentation clarity
- Consistency with project patterns

---

**Remember**: AgriSense helps farmers make data-driven decisions. Every feature should ultimately improve crop yields, reduce waste, or save time. Keep the end user in mind! 🌾
