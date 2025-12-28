# 🚀 AgriSense Full-Stack Hardware Optimization Implementation Guide

**Target Hardware**: Intel Core Ultra 9 275HX (32 threads) + RTX 5060 Laptop GPU (8GB)  
**Expected Performance**: 5-10x improvement in throughput, 3-5x lower latency  
**Difficulty**: Intermediate  
**Time**: 2-3 hours  

---

## Table of Contents
1. [Pre-Implementation Checklist](#pre-implementation-checklist)
2. [Backend Optimization](#backend-optimization)
3. [Frontend Optimization](#frontend-optimization)
4. [Database Optimization](#database-optimization)
5. [ML Inference Optimization](#ml-inference-optimization)
6. [Testing & Benchmarking](#testing--benchmarking)
7. [Monitoring & Validation](#monitoring--validation)
8. [Troubleshooting](#troubleshooting)

---

## Pre-Implementation Checklist

### ✅ Prerequisites
- [ ] Python 3.12.10 virtual environment active
- [ ] Node.js 18+ and npm installed
- [ ] NVIDIA drivers updated (latest for RTX 5060)
- [ ] CUDA Toolkit 12.4+ installed
- [ ] Git repository backed up
- [ ] At least 20GB free disk space

### 📦 Required Packages
```powershell
# Backend dependencies
pip install psutil GPUtil onnxruntime-gpu redis python-dotenv

# Frontend dependencies (in frontend directory)
cd agrisense_app/frontend/farm-fortune-frontend-main
npm install --save-dev vite-plugin-compression rollup-plugin-visualizer
```

---

## Backend Optimization

### Step 1: Update Environment Configuration

```powershell
# Copy optimized environment file
Copy-Item .env.production.optimized .env.production

# Update your current .env (or create if doesn't exist)
Copy-Item .env.production.optimized .env
```

**Verify critical variables**:
```powershell
# Check that these are set:
$env:UVICORN_WORKERS = 8
$env:OMP_NUM_THREADS = 24
$env:ML_NUM_WORKERS = 16
```

### Step 2: Integrate Performance Middleware

**File**: `agrisense_app/backend/main.py`

Add after imports (around line 30):
```python
# Hardware optimization middleware
try:
    from .middleware.performance import (
        PerformanceMonitoringMiddleware,
        IntelligentCachingMiddleware,
        LoadBalancingHintsMiddleware,
        warmup_models,
        get_system_metrics
    )
    MIDDLEWARE_AVAILABLE = True
except ImportError:
    MIDDLEWARE_AVAILABLE = False
    logger.warning("Performance middleware not available")
```

Add after `app = FastAPI(...)` (around line 500):
```python
# Add hardware-optimized middleware (order matters!)
if MIDDLEWARE_AVAILABLE:
    app.add_middleware(LoadBalancingHintsMiddleware, cpu_threshold=80.0)
    app.add_middleware(
        IntelligentCachingMiddleware,
        cache_ttl=300,
        max_cache_size=1000,
        cache_paths=["/api/sensors", "/api/analytics", "/api/recommendations"]
    )
    app.add_middleware(
        PerformanceMonitoringMiddleware,
        slow_request_threshold=1.0,
        enable_gpu_monitoring=True,
        log_all_requests=False  # Set True for debugging
    )
    logger.info("✅ Performance middleware enabled")
```

Add to startup event (find `@app.on_event("startup")` or create):
```python
@app.on_event("startup")
async def startup_optimizations():
    """Initialize hardware optimizations"""
    if MIDDLEWARE_AVAILABLE:
        logger.info("🚀 Initializing hardware optimizations...")
        
        # Warm up ML models
        await warmup_models()
        
        # Log system info
        metrics = get_system_metrics()
        logger.info(f"📊 System: CPU {metrics['cpu_percent']:.1f}% | "
                   f"RAM {metrics['memory_percent']:.1f}% | "
                   f"GPU {metrics.get('gpu_load_percent', 0):.1f}%")
```

### Step 3: Optimize ML Inference

**File**: `agrisense_app/backend/main.py` (or your ML module)

Add near ML imports:
```python
try:
    from .ml.inference_optimized import (
        initialize_ml_optimizations,
        get_model_cache,
        configure_tensorflow_performance,
        configure_pytorch_performance
    )
    ML_OPTIMIZATION_AVAILABLE = True
except ImportError:
    ML_OPTIMIZATION_AVAILABLE = False
```

Add to startup event:
```python
@app.on_event("startup")
async def startup_ml_optimizations():
    """Initialize ML framework optimizations"""
    if ML_OPTIMIZATION_AVAILABLE:
        initialize_ml_optimizations()
```

### Step 4: Update Uvicorn Startup

**Replace your current startup command** with the optimized one.

**Option A**: Use the optimized PowerShell script:
```powershell
.\start_optimized.ps1
```

**Option B**: Manual startup:
```powershell
python -m uvicorn agrisense_app.backend.main:app `
  --host 0.0.0.0 `
  --port 8004 `
  --workers 8 `
  --backlog 4096 `
  --limit-concurrency 2000 `
  --timeout-keep-alive 75 `
  --log-level info
```

**Option C**: Update your existing `start_agrisense.ps1`:
```powershell
# Find the uvicorn command and update parameters:
# Change: --workers 1 (or 4)
# To:     --workers 8 --backlog 4096 --limit-concurrency 2000
```

---

## Frontend Optimization

### Step 1: Update Vite Configuration

```powershell
cd agrisense_app/frontend/farm-fortune-frontend-main

# Backup current config
Copy-Item vite.config.ts vite.config.ts.backup

# Use optimized config
Copy-Item ../../../vite.config.optimized.ts vite.config.ts
```

### Step 2: Install Optimization Plugins

```powershell
npm install --save-dev vite-plugin-compression rollup-plugin-visualizer
```

### Step 3: Optimize Build Process

**Development** (fast rebuilds):
```powershell
npm run dev
```

**Production** (optimized bundle):
```powershell
# Build with all optimizations
npm run build

# Analyze bundle size
$env:ANALYZE="true"; npm run build

# Preview production build
npm run preview
```

### Step 4: Enable Service Worker (Optional)

For offline capability and faster loads:

```typescript
// src/main.tsx - add before ReactDOM.render

if ('serviceWorker' in navigator && import.meta.env.PROD) {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('/sw.js')
      .then(reg => console.log('✅ Service Worker registered'))
      .catch(err => console.log('❌ Service Worker failed:', err));
  });
}
```

---

## Database Optimization

### SQLite Optimization (Development)

**File**: `agrisense_app/backend/core/data_store.py`

Add to connection setup:
```python
import sqlite3

def init_sensor_db(db_path="sensors.db"):
    conn = sqlite3.connect(
        db_path,
        check_same_thread=False,
        timeout=30,
        isolation_level='DEFERRED',
        cached_statements=1000
    )
    
    # Enable performance features
    conn.execute('PRAGMA journal_mode=WAL')
    conn.execute('PRAGMA synchronous=NORMAL')
    conn.execute('PRAGMA cache_size=-64000')    # 64MB cache
    conn.execute('PRAGMA page_size=8192')       # 8KB pages
    conn.execute('PRAGMA temp_store=MEMORY')
    conn.execute('PRAGMA mmap_size=268435456')  # 256MB mmap
    conn.execute('PRAGMA threads=16')           # Use E-cores
    conn.execute('PRAGMA optimize')
    
    return conn
```

### PostgreSQL Optimization (Production)

**Install PostgreSQL** (if not already):
```powershell
# Using Chocolatey
choco install postgresql14

# Or download from: https://www.postgresql.org/download/windows/
```

**Configuration** (`C:\Program Files\PostgreSQL\14\data\postgresql.conf`):
```ini
# Memory (for 32GB RAM system)
shared_buffers = 8GB
effective_cache_size = 24GB
work_mem = 256MB
maintenance_work_mem = 2GB

# Parallelism (32 threads)
max_worker_processes = 32
max_parallel_workers_per_gather = 16
max_parallel_workers = 32

# Connections
max_connections = 200

# WAL
wal_level = replica
max_wal_size = 4GB
checkpoint_completion_target = 0.9

# SSD optimization
random_page_cost = 1.1
effective_io_concurrency = 200
```

**Restart PostgreSQL**:
```powershell
Restart-Service postgresql-x64-14
```

### Redis Setup (for caching)

**Install Redis** (Windows):
```powershell
# Using Chocolatey
choco install redis-64

# Or use Docker
docker run -d -p 6379:6379 redis:7-alpine
```

**Configure Redis** (`C:\Program Files\Redis\redis.windows.conf`):
```conf
# Memory
maxmemory 2gb
maxmemory-policy allkeys-lru

# Persistence (optional)
save 900 1
save 300 10
save 60 10000

# Network
bind 127.0.0.1
port 6379
```

---

## ML Inference Optimization

### Option 1: ONNX Runtime (Recommended)

**Install**:
```powershell
pip install onnxruntime-gpu  # For GPU
# OR
pip install onnxruntime-directml  # For DirectML (Windows GPU)
```

**Convert existing models to ONNX** (example):
```python
# For TensorFlow models
import tensorflow as tf
import tf2onnx

model = tf.keras.models.load_model('model.h5')
spec = (tf.TensorSpec((None, 10), tf.float32, name="input"),)
output_path = 'model.onnx'
model_proto, _ = tf2onnx.convert.from_keras(model, input_signature=spec)
with open(output_path, 'wb') as f:
    f.write(model_proto.SerializeToString())

# For PyTorch models
import torch

model = torch.load('model.pt')
dummy_input = torch.randn(1, 10)
torch.onnx.export(model, dummy_input, 'model.onnx')
```

**Use optimized inference**:
```python
from agrisense_app.backend.ml.inference_optimized import (
    ONNXModelOptimized,
    get_model_cache
)

# Load model (cached)
def load_model():
    return ONNXModelOptimized('models/disease_detection.onnx', use_gpu=True)

model = get_model_cache().get_or_load('disease_model', load_model)
prediction = model.predict(input_data)
```

### Option 2: TensorFlow with GPU

**Ensure GPU build** (may need Linux or WSL2 on Windows):
```powershell
pip install tensorflow[and-cuda]  # TF 2.15+
```

**Verify GPU**:
```python
import tensorflow as tf
print(tf.config.list_physical_devices('GPU'))
```

### Option 3: PyTorch with CUDA

**Already installed** (PyTorch 2.6.0+cu124):
```python
import torch
print(torch.cuda.is_available())  # Should be True
print(torch.cuda.get_device_name(0))  # RTX 5060
```

**Note**: RTX 5060 has sm_120, PyTorch max is sm_90. Models run but some optimizations unavailable.

---

## Testing & Benchmarking

### Step 1: Functional Testing

```powershell
# Start optimized backend
.\start_optimized.ps1

# In another terminal, test API
curl http://localhost:8004/health
curl http://localhost:8004/docs  # Should load OpenAPI docs
```

### Step 2: Load Testing

**Install Locust**:
```powershell
pip install locust
```

**Run load test**:
```powershell
# Basic test (500 users, 50/s spawn rate)
locust -f locustfile.py --host=http://localhost:8004 --users 500 --spawn-rate 50 --run-time 5m

# Stress test (2000 users - test 16K concurrent connections)
locust -f locustfile.py --host=http://localhost:8004 --users 2000 --spawn-rate 100 --run-time 10m
```

### Step 3: Performance Monitoring

**Monitor during load test**:
```powershell
# Terminal 1: CPU/Memory
while ($true) {
    Clear-Host
    Get-Process python | Select-Object CPU, WorkingSet64, Threads | Format-Table
    Start-Sleep 2
}

# Terminal 2: GPU
nvidia-smi dmon -s ucm -c 300 -d 1

# Terminal 3: Run load test
locust -f locustfile.py --host=http://localhost:8004 --headless --users 1000 --spawn-rate 50 --run-time 5m
```

### Step 4: Benchmark Results

**Expected metrics** (before vs after):

| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| Workers | 1-4 | 8 | 2-8x |
| Concurrent connections | ~100 | 16,000 | 160x |
| Avg latency (GET) | 200-500ms | 50-150ms | 3-5x |
| Throughput | 500-1000 req/s | 5000-10000 req/s | 5-10x |
| CPU utilization | 10-30% | 60-80% | Optimal |
| Memory usage | 2-4GB | 8-12GB | Efficient |

---

## Monitoring & Validation

### Built-in Monitoring

**With monitoring dashboard**:
```powershell
.\start_optimized.ps1 -Monitor
```

**Check performance headers**:
```powershell
curl -I http://localhost:8004/api/sensors
# Look for: X-Process-Time, X-CPU-Usage, X-GPU-Usage, X-Cache
```

### External Monitoring (Optional)

**Prometheus + Grafana**:
```powershell
# Install Prometheus
choco install prometheus

# Install Grafana
choco install grafana
```

**Add to `prometheus.yml`**:
```yaml
scrape_configs:
  - job_name: 'agrisense'
    static_configs:
      - targets: ['localhost:9090']
```

### Application Insights (Azure)

If deploying to Azure:
```python
# Add to requirements.txt
opencensus-ext-azure

# Add to main.py
from opencensus.ext.azure.trace_exporter import AzureExporter
from opencensus.trace.samplers import ProbabilitySampler
from opencensus.trace.tracer import Tracer

tracer = Tracer(
    exporter=AzureExporter(connection_string="..."),
    sampler=ProbabilitySampler(1.0)
)
```

---

## Troubleshooting

### Issue: PowerShell execution policy blocking scripts

**Symptoms**: "running scripts is disabled on this system" error

**Solutions**:
1. **Set policy for current user** (recommended):
   ```powershell
   Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
   ```

2. **Bypass for current session** (temporary):
   ```powershell
   Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope Process
   ```

3. **Use Python directly without activation**:
   ```powershell
   # Run commands using .venv Python directly
   .\.venv\Scripts\python.exe -m uvicorn agrisense_app.backend.main:app
   ```

4. **Run PowerShell as Administrator** and set system-wide policy:
   ```powershell
   Set-ExecutionPolicy -ExecutionPolicy RemoteSigned
   ```

### Issue: Backend won't start with 8 workers

**Symptoms**: Error about port already in use or workers crashing

**Solutions**:
1. Reduce workers: `$env:UVICORN_WORKERS=4`
2. Kill existing processes: `Get-Process python | Stop-Process`
3. Check port availability: `Test-NetConnection localhost -Port 8004`

### Issue: High memory usage (>16GB)

**Symptoms**: System slowdown, memory warnings

**Solutions**:
1. Reduce worker count: `--workers 4` instead of 8
2. Lower connection limits: `--limit-concurrency 1000`
3. Reduce cache sizes:
   ```bash
   MODEL_CACHE_SIZE=500
   CACHE_DEFAULT_TIMEOUT=1800
   ```

### Issue: GPU not detected

**Symptoms**: "No GPU detected" in logs, X-GPU-Usage header missing

**Solutions**:
1. Check CUDA: `nvidia-smi`
2. Update drivers: https://www.nvidia.com/Download/index.aspx
3. Reinstall onnxruntime: `pip install --force-reinstall onnxruntime-gpu`
4. Use DirectML: `pip install onnxruntime-directml`

### Issue: Slow requests despite optimization

**Symptoms**: X-Process-Time > 1.0s for simple requests

**Solutions**:
1. Check database: `PRAGMA optimize;` in SQLite
2. Review slow query logs: `LOG_SLOW_QUERIES=true`
3. Increase cache TTL: `CACHE_DEFAULT_TIMEOUT=3600`
4. Profile code:
   ```python
   import cProfile
   cProfile.run('your_function()')
   ```

### Issue: Frontend build fails

**Symptoms**: npm run build errors

**Solutions**:
1. Clear cache: `npm cache clean --force`
2. Reinstall: `rm -rf node_modules package-lock.json; npm install`
3. Check Node version: `node --version` (should be 18+)
4. Disable terser minification temporarily:
   ```typescript
   // vite.config.ts
   minify: 'esbuild',  // Instead of 'terser'
   ```

---

## Validation Checklist

After implementation, verify:

### Backend
- [ ] 8 Uvicorn workers running (`Get-Process python`)
- [ ] Performance headers in responses (`curl -I http://localhost:8004/api/sensors`)
- [ ] CPU usage 60-80% under load
- [ ] GPU detected in logs (if available)
- [ ] Cache working (X-Cache: HIT headers)
- [ ] Slow requests logged (check logs for ⚠️ SLOW)

### Frontend
- [ ] Build completes without errors
- [ ] Bundle size < 500KB per chunk (check dist/ folder)
- [ ] Lighthouse score > 90 (run in Chrome DevTools)
- [ ] HMR works in development (< 200ms updates)
- [ ] Production build loads in < 2s (test with throttling)

### Database
- [ ] SQLite WAL mode enabled (`PRAGMA journal_mode;` returns WAL)
- [ ] PostgreSQL parallelism working (check `SHOW max_parallel_workers;`)
- [ ] Redis connected (`redis-cli ping` returns PONG)

### ML Inference
- [ ] Models loaded at startup (check logs for "Loading model")
- [ ] GPU inference working (check X-GPU-Usage headers)
- [ ] Batch inference < 100ms for 128 samples
- [ ] Model cache working (second request faster than first)

---

## Performance Testing Script

**Create `test_optimization.ps1`**:
```powershell
#!/usr/bin/env pwsh
Write-Host "🧪 Testing AgriSense Optimization" -ForegroundColor Cyan

# 1. Check processes
Write-Host "`n📊 Backend Processes:" -ForegroundColor Yellow
Get-Process python -ErrorAction SilentlyContinue | Format-Table

# 2. Test API
Write-Host "`n🌐 API Health Check:" -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8004/health" -UseBasicParsing
    Write-Host "   ✅ Status: $($response.StatusCode)" -ForegroundColor Green
    Write-Host "   Headers:" -ForegroundColor Gray
    $response.Headers.GetEnumerator() | Where-Object { $_.Key -like "X-*" } | Format-Table
} catch {
    Write-Host "   ❌ API not responding" -ForegroundColor Red
}

# 3. Check GPU
Write-Host "`n🎮 GPU Status:" -ForegroundColor Yellow
try {
    nvidia-smi --query-gpu=name,utilization.gpu,memory.used --format=csv,noheader
} catch {
    Write-Host "   ⚠ GPU monitoring unavailable" -ForegroundColor Yellow
}

# 4. Quick load test
Write-Host "`n🚀 Quick Load Test (100 requests):" -ForegroundColor Yellow
$requests = 100
$url = "http://localhost:8004/health"
$times = @()

for ($i = 0; $i -lt $requests; $i++) {
    $start = Get-Date
    try {
        Invoke-WebRequest -Uri $url -UseBasicParsing -ErrorAction Stop | Out-Null
        $elapsed = ((Get-Date) - $start).TotalMilliseconds
        $times += $elapsed
    } catch {
        Write-Host "   ❌ Request failed" -ForegroundColor Red
    }
    
    if ($i % 20 -eq 0) {
        Write-Host "   Progress: $i/$requests" -ForegroundColor Gray
    }
}

$avg = ($times | Measure-Object -Average).Average
$min = ($times | Measure-Object -Minimum).Minimum
$max = ($times | Measure-Object -Maximum).Maximum
$p95 = ($times | Sort-Object)[[Math]::Floor($requests * 0.95)]

Write-Host "`n📈 Results:" -ForegroundColor Green
Write-Host "   Avg: $([Math]::Round($avg, 2))ms" -ForegroundColor White
Write-Host "   Min: $([Math]::Round($min, 2))ms" -ForegroundColor White
Write-Host "   Max: $([Math]::Round($max, 2))ms" -ForegroundColor White
Write-Host "   P95: $([Math]::Round($p95, 2))ms" -ForegroundColor White

if ($avg -lt 100) {
    Write-Host "`n✅ EXCELLENT: < 100ms average!" -ForegroundColor Green
} elseif ($avg -lt 200) {
    Write-Host "`n✅ GOOD: < 200ms average" -ForegroundColor Green
} else {
    Write-Host "`n⚠ NEEDS IMPROVEMENT: > 200ms average" -ForegroundColor Yellow
}
```

**Run**:
```powershell
.\test_optimization.ps1
```

---

## Next Steps

1. **Implement changes** following this guide
2. **Run tests** to validate improvements
3. **Monitor production** for 24-48 hours
4. **Fine-tune** based on real-world load
5. **Document** any custom adjustments

---

## Support & Resources

- **Documentation**: See `HARDWARE_OPTIMIZATION_CONFIG.md` for detailed specs
- **Monitoring**: Use `.\start_optimized.ps1 -Monitor` for real-time dashboard
- **Benchmarking**: Run `locustfile.py` for load testing
- **Profiling**: Use `cProfile` for Python, Chrome DevTools for frontend

---

**Created**: December 28, 2025  
**Hardware**: Intel Core Ultra 9 275HX (32 threads) + RTX 5060 (8GB)  
**Expected ROI**: 5-10x performance improvement  
**Status**: Ready for implementation ✅
