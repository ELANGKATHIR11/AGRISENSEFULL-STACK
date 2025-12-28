# 📊 AgriSense Monitoring & Error Tracking Setup

**Complete Guide for Production Monitoring**

**Version**: 1.0  
**Last Updated**: October 14, 2025  
**Target**: Production Deployment

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Sentry Integration](#sentry-integration)
3. [Prometheus Metrics](#prometheus-metrics)
4. [Grafana Dashboards](#grafana-dashboards)
5. [Log Aggregation](#log-aggregation)
6. [Alerting](#alerting)
7. [Performance Monitoring](#performance-monitoring)
8. [Error Tracking](#error-tracking)

---

## Overview

### Monitoring Stack

```
┌─────────────────────────────────────────────────┐
│           AgriSense Monitoring Stack            │
├─────────────────────────────────────────────────┤
│                                                 │
│  Application                                    │
│  ↓                                              │
│  Sentry (Error Tracking)                        │
│  ↓                                              │
│  Prometheus (Metrics Collection)                │
│  ↓                                              │
│  Grafana (Visualization)                        │
│  ↓                                              │
│  Alertmanager (Notifications)                   │
│                                                 │
└─────────────────────────────────────────────────┘
```

### Metrics to Monitor

| Category | Metrics | Tools |
|----------|---------|-------|
| **Performance** | Response time, throughput, latency | Prometheus, Grafana |
| **Errors** | Error rate, exception traces, stack traces | Sentry |
| **Resources** | CPU, memory, disk, network | Prometheus Node Exporter |
| **Business** | Recommendations generated, images analyzed | Custom metrics |
| **Availability** | Uptime, health checks | Prometheus Blackbox |

---

## Sentry Integration

### Backend Setup (FastAPI)

#### 1. Install Sentry SDK

```bash
pip install sentry-sdk[fastapi]
```

#### 2. Configure in `main.py`

```python
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.starlette import StarletteIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
import os

# Initialize Sentry
sentry_sdk.init(
    dsn=os.getenv("SENTRY_DSN"),
    environment=os.getenv("AGRISENSE_ENV", "development"),
    release=f"agrisense-backend@{os.getenv('APP_VERSION', '1.0.0')}",
    
    # Integrations
    integrations=[
        FastApiIntegration(),
        StarletteIntegration(),
        SqlalchemyIntegration(),
    ],
    
    # Performance monitoring
    traces_sample_rate=0.1,  # 10% of transactions
    
    # Filter sensitive data
    before_send=filter_sensitive_data,
    
    # Set max breadcrumbs
    max_breadcrumbs=50,
    
    # Debug mode (disable in production)
    debug=os.getenv("SENTRY_DEBUG", "false").lower() == "true",
)

def filter_sensitive_data(event, hint):
    """Filter sensitive information from error reports"""
    # Remove passwords
    if "request" in event:
        if "data" in event["request"]:
            data = event["request"]["data"]
            if isinstance(data, dict):
                for key in ["password", "token", "secret", "api_key"]:
                    if key in data:
                        data[key] = "[Filtered]"
    
    # Remove image data (too large)
    if "extra" in event:
        if "image_base64" in event["extra"]:
            event["extra"]["image_base64"] = "[Image data removed]"
    
    return event

# Add context to errors
@app.middleware("http")
async def add_sentry_context(request: Request, call_next):
    with sentry_sdk.configure_scope() as scope:
        scope.set_tag("path", request.url.path)
        scope.set_tag("method", request.method)
        scope.set_context("request", {
            "url": str(request.url),
            "method": request.method,
            "headers": dict(request.headers),
        })
    
    response = await call_next(request)
    return response

# Capture custom errors
from sentry_sdk import capture_exception, capture_message

@app.post("/api/example")
async def example_endpoint():
    try:
        # Your code
        result = risky_operation()
        return result
    except ValueError as e:
        # Capture with context
        with sentry_sdk.push_scope() as scope:
            scope.set_tag("operation", "risky_operation")
            scope.set_extra("details", "More context")
            capture_exception(e)
        raise HTTPException(status_code=400, detail=str(e))
```

### Frontend Setup (React)

#### 1. Install Sentry SDK

```bash
npm install @sentry/react @sentry/tracing
```

#### 2. Configure in `main.tsx`

```typescript
import * as Sentry from "@sentry/react";
import { BrowserTracing } from "@sentry/tracing";

Sentry.init({
  dsn: import.meta.env.VITE_SENTRY_DSN,
  environment: import.meta.env.MODE,
  release: `agrisense-frontend@${import.meta.env.VITE_APP_VERSION}`,
  
  integrations: [
    new BrowserTracing({
      tracingOrigins: ["localhost", "yourdomain.com", /^\//],
      routingInstrumentation: Sentry.reactRouterV6Instrumentation(
        React.useEffect,
        useLocation,
        useNavigationType,
        createRoutesFromChildren,
        matchRoutes
      ),
    }),
  ],
  
  // Performance monitoring
  tracesSampleRate: 0.1,
  
  // Session replay (optional)
  replaysSessionSampleRate: 0.1,
  replaysOnErrorSampleRate: 1.0,
  
  // Filter sensitive data
  beforeSend(event, hint) {
    // Remove PII
    if (event.request?.data) {
      const data = event.request.data as any;
      if (data.password) data.password = "[Filtered]";
      if (data.email) data.email = "[Filtered]";
    }
    return event;
  },
});

// Error boundary
const App = () => (
  <Sentry.ErrorBoundary fallback={<ErrorFallback />}>
    <YourApp />
  </Sentry.ErrorBoundary>
);

// Manual error capture
import { captureException } from "@sentry/react";

try {
  await uploadImage(file);
} catch (error) {
  captureException(error, {
    tags: { feature: "image-upload" },
    extra: { fileSize: file.size },
  });
  showError("Upload failed");
}
```

---

## Prometheus Metrics

### Backend Metrics

#### 1. Install Prometheus Client

```bash
pip install prometheus-client
```

#### 2. Add Metrics to `main.py`

```python
from prometheus_client import Counter, Histogram, Gauge, generate_latest
from prometheus_client import CollectorRegistry, CONTENT_TYPE_LATEST
from fastapi import Response
import time

# Create registry
registry = CollectorRegistry()

# Define metrics
request_count = Counter(
    'agrisense_http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status'],
    registry=registry
)

request_duration = Histogram(
    'agrisense_http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint'],
    registry=registry,
    buckets=(0.01, 0.05, 0.1, 0.5, 1.0, 2.0, 5.0, 10.0)
)

active_requests = Gauge(
    'agrisense_http_requests_active',
    'Number of active HTTP requests',
    registry=registry
)

# ML model metrics
ml_inference_count = Counter(
    'agrisense_ml_inferences_total',
    'Total ML model inferences',
    ['model_type', 'status'],
    registry=registry
)

ml_inference_duration = Histogram(
    'agrisense_ml_inference_duration_seconds',
    'ML inference duration',
    ['model_type'],
    registry=registry,
    buckets=(0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0)
)

# Business metrics
recommendations_count = Counter(
    'agrisense_recommendations_total',
    'Total recommendations generated',
    ['type'],
    registry=registry
)

disease_detections = Counter(
    'agrisense_disease_detections_total',
    'Disease detection attempts',
    ['status', 'disease'],
    registry=registry
)

# Middleware for request tracking
@app.middleware("http")
async def prometheus_middleware(request: Request, call_next):
    # Track active requests
    active_requests.inc()
    
    # Record start time
    start_time = time.time()
    
    try:
        # Process request
        response = await call_next(request)
        
        # Record metrics
        duration = time.time() - start_time
        
        request_count.labels(
            method=request.method,
            endpoint=request.url.path,
            status=response.status_code
        ).inc()
        
        request_duration.labels(
            method=request.method,
            endpoint=request.url.path
        ).observe(duration)
        
        # Add timing header
        response.headers["X-Process-Time"] = str(duration)
        
        return response
    
    finally:
        active_requests.dec()

# Metrics endpoint
@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    return Response(
        content=generate_latest(registry),
        media_type=CONTENT_TYPE_LATEST
    )

# Track ML inferences
async def detect_disease(image_data: str):
    start = time.time()
    try:
        result = await ml_model.detect(image_data)
        
        # Record success
        ml_inference_count.labels(
            model_type="disease_detection",
            status="success"
        ).inc()
        
        disease_detections.labels(
            status="detected",
            disease=result.get("disease", "unknown")
        ).inc()
        
        return result
    
    except Exception as e:
        # Record failure
        ml_inference_count.labels(
            model_type="disease_detection",
            status="error"
        ).inc()
        raise
    
    finally:
        duration = time.time() - start
        ml_inference_duration.labels(
            model_type="disease_detection"
        ).observe(duration)

# Track business metrics
@app.post("/api/v1/irrigation/recommend")
async def get_recommendation(data: SensorData):
    result = engine.recommend(data.dict())
    
    # Track recommendation
    recommendations_count.labels(type="irrigation").inc()
    
    return result
```

#### 3. System Metrics with Node Exporter

```bash
# Install Node Exporter
wget https://github.com/prometheus/node_exporter/releases/download/v1.6.1/node_exporter-1.6.1.linux-amd64.tar.gz
tar xvfz node_exporter-1.6.1.linux-amd64.tar.gz
cd node_exporter-1.6.1.linux-amd64
./node_exporter &

# Metrics available at http://localhost:9100/metrics
```

#### 4. Prometheus Configuration

Create `prometheus.yml`:

```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  # AgriSense Backend
  - job_name: 'agrisense-backend'
    static_configs:
      - targets: ['localhost:8004']
    metrics_path: '/metrics'
  
  # System metrics
  - job_name: 'node'
    static_configs:
      - targets: ['localhost:9100']
  
  # Blackbox exporter (uptime monitoring)
  - job_name: 'blackbox'
    metrics_path: /probe
    params:
      module: [http_2xx]
    static_configs:
      - targets:
          - https://yourdomain.com
          - https://yourdomain.com/health
    relabel_configs:
      - source_labels: [__address__]
        target_label: __param_target
      - source_labels: [__param_target]
        target_label: instance
      - target_label: __address__
        replacement: localhost:9115

# Alerting rules
rule_files:
  - 'alerts.yml'

# Alertmanager configuration
alerting:
  alertmanagers:
    - static_configs:
        - targets: ['localhost:9093']
```

---

## Grafana Dashboards

### 1. Install Grafana

```bash
# Ubuntu/Debian
sudo apt-get install -y software-properties-common
sudo add-apt-repository "deb https://packages.grafana.com/oss/deb stable main"
wget -q -O - https://packages.grafana.com/gpg.key | sudo apt-key add -
sudo apt-get update
sudo apt-get install grafana

sudo systemctl start grafana-server
sudo systemctl enable grafana-server

# Access at http://localhost:3000
# Default credentials: admin/admin
```

### 2. Configure Prometheus Data Source

1. Go to Configuration → Data Sources
2. Add Prometheus
3. URL: `http://localhost:9090`
4. Save & Test

### 3. Create AgriSense Dashboard

#### Panel 1: Request Rate
```promql
rate(agrisense_http_requests_total[5m])
```

#### Panel 2: Response Time (95th percentile)
```promql
histogram_quantile(0.95, rate(agrisense_http_request_duration_seconds_bucket[5m]))
```

#### Panel 3: Error Rate
```promql
rate(agrisense_http_requests_total{status=~"5.."}[5m])
```

#### Panel 4: Active Requests
```promql
agrisense_http_requests_active
```

#### Panel 5: ML Inference Time
```promql
histogram_quantile(0.95, rate(agrisense_ml_inference_duration_seconds_bucket[5m]))
```

#### Panel 6: Recommendations per Hour
```promql
increase(agrisense_recommendations_total[1h])
```

#### Panel 7: Disease Detections
```promql
sum(rate(agrisense_disease_detections_total[5m])) by (disease)
```

#### Panel 8: System Resources
```promql
# CPU Usage
100 - (avg by (instance) (irate(node_cpu_seconds_total{mode="idle"}[5m])) * 100)

# Memory Usage
100 * (1 - ((node_memory_MemAvailable_bytes) / (node_memory_MemTotal_bytes)))

# Disk Usage
100 - ((node_filesystem_avail_bytes{mountpoint="/"} * 100) / node_filesystem_size_bytes{mountpoint="/"})
```

### 4. Import Dashboard JSON

Save as `agrisense-dashboard.json`:

```json
{
  "dashboard": {
    "title": "AgriSense Production Metrics",
    "panels": [
      {
        "title": "Request Rate",
        "targets": [
          {
            "expr": "rate(agrisense_http_requests_total[5m])"
          }
        ],
        "type": "graph"
      },
      {
        "title": "95th Percentile Response Time",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(agrisense_http_request_duration_seconds_bucket[5m]))"
          }
        ],
        "type": "graph"
      }
    ]
  }
}
```

Import: Dashboards → Import → Upload JSON

---

## Log Aggregation

### Structured Logging

#### Backend Logging Setup

```python
import logging
import json
from datetime import datetime
import sys

class JSONFormatter(logging.Formatter):
    """Format logs as JSON for easy parsing"""
    
    def format(self, record):
        log_obj = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Add exception info
        if record.exc_info:
            log_obj["exception"] = self.formatException(record.exc_info)
        
        # Add extra fields
        if hasattr(record, "user_id"):
            log_obj["user_id"] = record.user_id
        if hasattr(record, "request_id"):
            log_obj["request_id"] = record.request_id
        
        return json.dumps(log_obj)

# Configure logging
def setup_logging():
    logger = logging.getLogger("agrisense")
    logger.setLevel(logging.INFO)
    
    # Console handler (JSON format)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(JSONFormatter())
    logger.addHandler(console_handler)
    
    # File handler (rotating)
    from logging.handlers import RotatingFileHandler
    file_handler = RotatingFileHandler(
        "/var/log/agrisense/app.log",
        maxBytes=10485760,  # 10MB
        backupCount=5
    )
    file_handler.setFormatter(JSONFormatter())
    logger.addHandler(file_handler)
    
    return logger

logger = setup_logging()

# Usage with context
logger.info("Processing recommendation", extra={
    "user_id": user_id,
    "request_id": request_id,
    "sensor_data": sensor_data
})
```

### Log Analysis with ELK Stack (Optional)

```bash
# Install Elasticsearch, Logstash, Kibana
# Then configure Filebeat to ship logs

# filebeat.yml
filebeat.inputs:
  - type: log
    enabled: true
    paths:
      - /var/log/agrisense/*.log
    json.keys_under_root: true
    json.add_error_key: true

output.elasticsearch:
  hosts: ["localhost:9200"]
  index: "agrisense-logs-%{+yyyy.MM.dd}"
```

---

## Alerting

### Alertmanager Configuration

Create `alerts.yml`:

```yaml
groups:
  - name: agrisense_alerts
    interval: 30s
    rules:
      # High error rate
      - alert: HighErrorRate
        expr: rate(agrisense_http_requests_total{status=~"5.."}[5m]) > 0.05
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "High error rate detected"
          description: "Error rate is {{ $value }} errors/sec"
      
      # Slow response time
      - alert: SlowResponseTime
        expr: histogram_quantile(0.95, rate(agrisense_http_request_duration_seconds_bucket[5m])) > 2
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "Slow response time"
          description: "95th percentile response time is {{ $value }}s"
      
      # High memory usage
      - alert: HighMemoryUsage
        expr: 100 * (1 - ((node_memory_MemAvailable_bytes) / (node_memory_MemTotal_bytes))) > 85
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High memory usage"
          description: "Memory usage is {{ $value }}%"
      
      # Service down
      - alert: ServiceDown
        expr: up{job="agrisense-backend"} == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "AgriSense backend is down"
          description: "Backend service has been down for 1 minute"
      
      # ML inference too slow
      - alert: SlowMLInference
        expr: histogram_quantile(0.95, rate(agrisense_ml_inference_duration_seconds_bucket[5m])) > 10
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "ML inference is slow"
          description: "95th percentile inference time is {{ $value }}s"
```

### Alertmanager Configuration

Create `alertmanager.yml`:

```yaml
global:
  smtp_from: 'alerts@agrisense.example'
  smtp_smarthost: 'smtp.gmail.com:587'
  smtp_auth_username: 'your-email@gmail.com'
  smtp_auth_password: 'your-app-password'

route:
  receiver: 'team-email'
  group_by: ['alertname']
  group_wait: 30s
  group_interval: 5m
  repeat_interval: 4h
  
  routes:
    - match:
        severity: critical
      receiver: 'team-pager'
      continue: true
    
    - match:
        severity: warning
      receiver: 'team-email'

receivers:
  - name: 'team-email'
    email_configs:
      - to: 'team@agrisense.example'
        headers:
          Subject: '[AgriSense Alert] {{ .GroupLabels.alertname }}'
  
  - name: 'team-pager'
    webhook_configs:
      - url: 'https://your-pagerduty-webhook'
```

---

## Performance Monitoring

### Real User Monitoring (RUM)

#### Frontend Performance Tracking

```typescript
// performance.ts
export function trackPerformance() {
  if ('performance' in window) {
    window.addEventListener('load', () => {
      const perfData = window.performance.timing;
      const pageLoadTime = perfData.loadEventEnd - perfData.navigationStart;
      const connectTime = perfData.responseEnd - perfData.requestStart;
      const renderTime = perfData.domComplete - perfData.domLoading;
      
      // Send to analytics
      analytics.track('page_performance', {
        page_load_time: pageLoadTime,
        connect_time: connectTime,
        render_time: renderTime,
        url: window.location.pathname,
      });
      
      // Also send to Sentry
      Sentry.setMeasurement('page_load_time', pageLoadTime, 'millisecond');
    });
  }
}

// Track custom timing
export function measureOperation(name: string, fn: () => void) {
  const start = performance.now();
  fn();
  const duration = performance.now() - start;
  
  Sentry.setMeasurement(name, duration, 'millisecond');
}
```

### Core Web Vitals

```typescript
import { getCLS, getFID, getFCP, getLCP, getTTFB } from 'web-vitals';

function sendToAnalytics(metric: any) {
  const body = JSON.stringify({
    name: metric.name,
    value: metric.value,
    id: metric.id,
    url: window.location.href,
  });
  
  // Send to your analytics endpoint
  if (navigator.sendBeacon) {
    navigator.sendBeacon('/api/analytics/vitals', body);
  }
}

getCLS(sendToAnalytics);
getFID(sendToAnalytics);
getFCP(sendToAnalytics);
getLCP(sendToAnalytics);
getTTFB(sendToAnalytics);
```

---

## Error Tracking

### Error Categories

1. **Application Errors**
   - Python exceptions
   - JavaScript errors
   - API errors

2. **Integration Errors**
   - Database connection failures
   - External API failures
   - ML model errors

3. **User Errors**
   - Validation errors
   - Authentication failures
   - Permission errors

### Error Severity Levels

```python
# In Sentry
sentry_sdk.set_level("error")  # error, warning, info, debug

# With context
with sentry_sdk.push_scope() as scope:
    scope.level = "fatal"  # fatal, error, warning, info, debug
    scope.set_tag("feature", "disease_detection")
    capture_exception(exception)
```

### Error Fingerprinting

```python
# Custom fingerprint for grouping
@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    with sentry_sdk.push_scope() as scope:
        scope.fingerprint = ["value-error", request.url.path]
        capture_exception(exc)
    
    return JSONResponse(
        status_code=400,
        content={"detail": str(exc)}
    )
```

---

## Quick Reference

### Essential Commands

```bash
# Check Prometheus targets
curl http://localhost:9090/api/v1/targets

# Query metric
curl 'http://localhost:9090/api/v1/query?query=agrisense_http_requests_total'

# Check Grafana health
curl http://localhost:3000/api/health

# View recent errors in Sentry
# Go to https://sentry.io/organizations/your-org/issues/

# Check alertmanager status
curl http://localhost:9093/api/v1/status
```

### Useful PromQL Queries

```promql
# Average response time
rate(agrisense_http_request_duration_seconds_sum[5m]) / rate(agrisense_http_request_duration_seconds_count[5m])

# Request rate per endpoint
sum(rate(agrisense_http_requests_total[5m])) by (endpoint)

# Error percentage
100 * sum(rate(agrisense_http_requests_total{status=~"5.."}[5m])) / sum(rate(agrisense_http_requests_total[5m]))

# Top 5 slowest endpoints
topk(5, histogram_quantile(0.95, rate(agrisense_http_request_duration_seconds_bucket[5m]))) by (endpoint)
```

---

**Last Updated**: October 14, 2025  
**Maintained By**: AgriSense DevOps Team  
**Version**: 1.0
