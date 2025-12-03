# 🚀 AgriSense Production Deployment Guide

**Last Updated**: January 2025  
**Version**: 1.0.0  
**Status**: Production Ready ✅

---

## 📋 Table of Contents

1. [Prerequisites](#prerequisites)
2. [Docker Containerization](#docker-containerization)
3. [CI/CD Pipeline](#cicd-pipeline)
4. [Database Migration](#database-migration)
5. [Monitoring & Alerting](#monitoring--alerting)
6. [Backup Strategy](#backup-strategy)
7. [SSL/TLS Configuration](#ssltls-configuration)
8. [Rate Limiting](#rate-limiting)
9. [Security Best Practices](#security-best-practices)
10. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### System Requirements

**Production Server**:
- **OS**: Ubuntu 22.04 LTS or RHEL 8+
- **CPU**: 4+ cores (8+ recommended for ML workloads)
- **RAM**: 16GB minimum (32GB recommended)
- **Storage**: 100GB+ SSD (500GB+ for ML models and data)
- **Network**: Static IP, open ports 80, 443, 8004

**Development Machine**:
- Docker 24.0+
- Docker Compose 2.20+
- Git 2.40+
- Node.js 18+
- Python 3.9+

### Required Secrets

Create these GitHub Secrets before deployment:

```bash
# Production Server Access
PROD_HOST=your-production-server.com
PROD_USER=deploy
PROD_SSH_KEY=<SSH private key>

# Staging Server Access
STAGING_HOST=staging.agrisense.com
STAGING_USER=deploy
STAGING_SSH_KEY=<SSH private key>

# Notifications
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...

# Database
POSTGRES_PASSWORD=<strong-password>

# Application Secrets
AGRISENSE_ADMIN_TOKEN=<secure-random-token>
JWT_SECRET_KEY=<secure-random-key>
```

---

## Docker Containerization

### Quick Start

**Development Environment**:
```powershell
cd AGRISENSEFULL-STACK

# Start all services
docker-compose -f docker-compose.dev.yml up -d

# View logs
docker-compose -f docker-compose.dev.yml logs -f backend

# Stop services
docker-compose -f docker-compose.dev.yml down
```

**Production Environment**:
```bash
cd AGRISENSEFULL-STACK

# Set environment variables
export POSTGRES_PASSWORD="your-secure-password"
export AGRISENSE_ADMIN_TOKEN="your-admin-token"

# Start all services
docker-compose up -d

# Check health
curl http://localhost:8004/health
curl http://localhost:80/health

# View logs
docker-compose logs -f
```

### Architecture

```
┌─────────────────────────────────────────────────────┐
│                   Nginx Frontend                    │
│              (Static Files + Proxy)                 │
│                   Port 80/443                       │
└──────────────────────┬──────────────────────────────┘
                       │ Reverse Proxy
┌──────────────────────▼──────────────────────────────┐
│              FastAPI Backend                        │
│         (4 Uvicorn Workers)                         │
│                Port 8004                            │
└──────────────┬──────────────┬───────────────────────┘
               │              │
      ┌────────▼────┐   ┌─────▼──────┐
      │  PostgreSQL │   │   Redis    │
      │  Database   │   │   Cache    │
      │  Port 5432  │   │ Port 6379  │
      └─────────────┘   └────────────┘
```

### Service Configuration

**Backend Service** (`Dockerfile`):
- Multi-stage build (builder + runtime)
- Non-root user (`agrisense`)
- Health checks every 30s
- 4 Uvicorn workers
- ML models mounted as volumes
- Logs to `/app/logs`

**Frontend Service** (`Dockerfile.frontend`):
- Vite production build
- Nginx Alpine (minimal)
- Gzip compression enabled
- Security headers configured
- API proxy to backend
- Health endpoint at `/health`

**PostgreSQL Service**:
- Alpine Linux base
- Persistent data volume
- Automatic schema initialization
- Health checks with `pg_isready`

**Redis Service**:
- Alpine Linux base
- AOF persistence enabled
- Health checks with `redis-cli ping`

### Build Images Locally

```bash
# Backend
docker build -f Dockerfile -t agrisense-backend:latest .

# Frontend
docker build -f Dockerfile.frontend -t agrisense-frontend:latest .

# Test images
docker run -p 8004:8004 agrisense-backend:latest
docker run -p 80:80 agrisense-frontend:latest
```

### Docker Compose Files

| File | Purpose | Use Case |
|------|---------|----------|
| `docker-compose.yml` | Production setup | Deployment to servers |
| `docker-compose.dev.yml` | Development setup | Local development with hot reload |
| `docker-compose.monitoring.yml` | Monitoring stack | Prometheus + Grafana (see Monitoring section) |

---

## CI/CD Pipeline

### GitHub Actions Workflows

#### 1. **CI Workflow** (`.github/workflows/ci.yml`)

**Triggers**:
- Pull requests to `main` or `develop`
- Pushes to `develop`
- Weekly security scans (Sunday midnight)

**Jobs**:
1. **Security Scan**:
   - pip-audit for Python dependencies
   - safety check for known vulnerabilities
   - Uploads reports as artifacts

2. **Linting**:
   - Black formatter check
   - Flake8 code quality
   - isort import sorting

3. **Unit Tests**:
   - pytest with coverage
   - ML disabled for speed
   - Uploads coverage to Codecov

4. **Integration Tests**:
   - Redis service container
   - Backend startup
   - Full API testing

5. **Frontend Tests**:
   - npm audit
   - ESLint
   - TypeScript compilation
   - Production build

6. **Performance Tests** (main branch only):
   - Locust load testing
   - 50 concurrent users
   - 2-minute run
   - HTML report generated

#### 2. **CD Workflow** (`.github/workflows/cd.yml`)

**Triggers**:
- Pushes to `main` branch
- Manual workflow dispatch for production

**Jobs**:
1. **Build & Push**:
   - Builds Docker images for both platforms (amd64, arm64)
   - Pushes to GitHub Container Registry (ghcr.io)
   - Tags with commit SHA and semantic versions

2. **Deploy Staging** (automatic):
   - SSH to staging server
   - Pull latest images
   - Rolling update (backend first, then frontend)
   - Health checks
   - Smoke tests

3. **Deploy Production** (manual approval):
   - Requires workflow dispatch trigger
   - Database backup before deployment
   - Rolling update strategy
   - Health checks
   - Smoke tests
   - Slack notifications

4. **Rollback** (on failure):
   - Automatically triggered if production deploy fails
   - Restores previous Docker images
   - Notifies team

#### 3. **Docker Build Workflow** (`.github/workflows/docker-build.yml`)

**Triggers**:
- Changes to Dockerfiles or compose files
- Weekly Monday 6 AM security scans

**Jobs**:
1. **Build Backend**:
   - Multi-platform build (amd64, arm64)
   - Trivy vulnerability scan
   - Grype security scan
   - Upload SARIF to GitHub Security

2. **Build Frontend**:
   - Multi-platform build
   - Trivy vulnerability scan
   - Upload SARIF to GitHub Security

3. **Test Compose**:
   - Validate docker-compose.yml syntax
   - Start all services
   - Health checks
   - Log analysis

### Branch Protection Rules

Configure in GitHub repository settings:

```yaml
Branch: main
- Require pull request reviews (1 reviewer)
- Require status checks to pass:
  ✓ security-scan
  ✓ lint
  ✓ unit-tests
  ✓ integration-tests
  ✓ frontend-tests
- Require branches to be up to date
- Restrict who can push to matching branches
```

### Deployment Workflow

```mermaid
graph LR
    A[Developer Push] --> B[Create PR]
    B --> C[CI Tests Run]
    C --> D{Tests Pass?}
    D -->|No| E[Fix Issues]
    E --> B
    D -->|Yes| F[Code Review]
    F --> G[Merge to Main]
    G --> H[Build Images]
    H --> I[Deploy Staging]
    I --> J{Staging OK?}
    J -->|No| K[Rollback]
    J -->|Yes| L[Manual Approval]
    L --> M[Deploy Production]
    M --> N{Production OK?}
    N -->|No| O[Auto Rollback]
    N -->|Yes| P[Notify Success]
```

---

## Database Migration

### PostgreSQL Setup

**Initial Database Creation**:

The `scripts/init-db.sql` file automatically runs on first container startup:

```sql
-- Tables created:
- sensor_readings        (IoT device data)
- irrigation_logs        (Watering actions)
- crop_recommendations   (ML predictions)
- disease_detections     (Disease analysis)
- weed_detections        (Weed analysis)
- chatbot_interactions   (User queries)
- users                  (Authentication - future)
```

**Connect to Database**:
```bash
# From host machine
docker exec -it agrisense-postgres psql -U agrisense -d agrisense_db

# Inside container
docker-compose exec postgres psql -U agrisense -d agrisense_db
```

### Alembic Migration Setup

**Install Alembic**:
```bash
cd AGRISENSEFULL-STACK/agrisense_app/backend
pip install alembic asyncpg
```

**Initialize Alembic**:
```bash
alembic init alembic
```

**Configure `alembic.ini`**:
```ini
# alembic.ini
sqlalchemy.url = postgresql://agrisense:password@localhost:5432/agrisense_db

# Or use environment variable:
# sqlalchemy.url = ${DATABASE_URL}
```

**Configure `alembic/env.py`**:
```python
# Import your models
from agrisense_app.backend import models

# Set target metadata
target_metadata = models.Base.metadata

# Use async engine for PostgreSQL
from sqlalchemy.ext.asyncio import create_async_engine

config.set_main_option(
    'sqlalchemy.url',
    os.environ.get('DATABASE_URL', 'postgresql://agrisense:password@localhost:5432/agrisense_db')
)
```

### Create Migrations

```bash
# Auto-generate migration from model changes
alembic revision --autogenerate -m "Add new column to sensor_readings"

# Create empty migration for manual edits
alembic revision -m "Custom migration"

# Apply migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1

# View migration history
alembic history
```

### SQLite to PostgreSQL Migration Script

```python
# scripts/migrate_sqlite_to_postgres.py
import sqlite3
import psycopg2
from psycopg2.extras import execute_values

def migrate_sensor_data():
    # Connect to SQLite
    sqlite_conn = sqlite3.connect('agrisense_app/backend/sensors.db')
    sqlite_cursor = sqlite_conn.cursor()
    
    # Connect to PostgreSQL
    pg_conn = psycopg2.connect(
        host='localhost',
        port=5432,
        user='agrisense',
        password='changeme',
        database='agrisense_db'
    )
    pg_cursor = pg_conn.cursor()
    
    # Fetch data from SQLite
    sqlite_cursor.execute("SELECT * FROM sensor_readings")
    rows = sqlite_cursor.fetchall()
    
    # Insert into PostgreSQL
    execute_values(
        pg_cursor,
        "INSERT INTO sensor_readings (device_id, timestamp, temperature, humidity, soil_moisture, ph_level, nitrogen, phosphorus, potassium, rainfall) VALUES %s",
        rows
    )
    
    pg_conn.commit()
    sqlite_conn.close()
    pg_conn.close()
    print(f"Migrated {len(rows)} rows")

if __name__ == '__main__':
    migrate_sensor_data()
```

---

## Monitoring & Alerting

### Prometheus + Grafana Stack

**Create `docker-compose.monitoring.yml`**:
```yaml
version: '3.8'

services:
  prometheus:
    image: prom/prometheus:latest
    container_name: prometheus
    volumes:
      - ./docker/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
    ports:
      - "9090:9090"
    networks:
      - agrisense-network

  grafana:
    image: grafana/grafana:latest
    container_name: grafana
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
      - GF_INSTALL_PLUGINS=grafana-piechart-panel
    volumes:
      - grafana_data:/var/lib/grafana
      - ./docker/grafana/dashboards:/etc/grafana/provisioning/dashboards
      - ./docker/grafana/datasources:/etc/grafana/provisioning/datasources
    ports:
      - "3000:3000"
    networks:
      - agrisense-network

  alertmanager:
    image: prom/alertmanager:latest
    container_name: alertmanager
    volumes:
      - ./docker/alertmanager.yml:/etc/alertmanager/alertmanager.yml
    command:
      - '--config.file=/etc/alertmanager/alertmanager.yml'
    ports:
      - "9093:9093"
    networks:
      - agrisense-network

volumes:
  prometheus_data:
  grafana_data:

networks:
  agrisense-network:
    external: true
```

**Start Monitoring Stack**:
```bash
docker-compose -f docker-compose.yml -f docker-compose.monitoring.yml up -d
```

**Access Dashboards**:
- Grafana: http://localhost:3000 (admin/admin)
- Prometheus: http://localhost:9090
- Alertmanager: http://localhost:9093

### Backend Metrics Endpoint

Already implemented in `agrisense_app/backend/main.py`:

```python
@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    return Response(
        content=generate_latest(),
        media_type="text/plain"
    )
```

**Key Metrics Exposed**:
- `http_requests_total` - Request counter
- `http_request_duration_seconds` - Request latency
- `active_connections` - Current connections
- `ml_inference_duration_seconds` - ML model latency
- `database_query_duration_seconds` - DB query time

### Alerting Rules

**Create `docker/alerting-rules.yml`**:
```yaml
groups:
  - name: agrisense_alerts
    interval: 30s
    rules:
      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.05
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "High error rate detected"
          description: "Error rate is {{ $value }} errors/sec"

      - alert: HighLatency
        expr: http_request_duration_seconds{quantile="0.95"} > 2
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High API latency"
          description: "95th percentile latency is {{ $value }}s"

      - alert: DatabaseDown
        expr: up{job="postgres"} == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "PostgreSQL database is down"

      - alert: DiskSpaceRunningOut
        expr: (node_filesystem_avail_bytes / node_filesystem_size_bytes) < 0.1
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "Disk space below 10%"
```

---

## Backup Strategy

### Automated Database Backups

**Create `scripts/backup-postgres.sh`**:
```bash
#!/bin/bash
# backup-postgres.sh - Automated PostgreSQL backup

BACKUP_DIR="/opt/agrisense/backups/postgres"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/agrisense_backup_$TIMESTAMP.sql"
RETENTION_DAYS=30

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Perform backup
docker exec agrisense-postgres pg_dump -U agrisense agrisense_db > "$BACKUP_FILE"

# Compress backup
gzip "$BACKUP_FILE"

# Remove old backups
find "$BACKUP_DIR" -name "agrisense_backup_*.sql.gz" -mtime +$RETENTION_DAYS -delete

echo "Backup completed: ${BACKUP_FILE}.gz"
```

**Make executable and set up cron**:
```bash
chmod +x scripts/backup-postgres.sh

# Add to crontab (daily at 2 AM)
crontab -e
0 2 * * * /opt/agrisense/scripts/backup-postgres.sh >> /var/log/agrisense-backup.log 2>&1
```

### ML Model Backups

**Create `scripts/backup-ml-models.sh`**:
```bash
#!/bin/bash
# backup-ml-models.sh - Backup ML model artifacts

MODELS_DIR="/opt/agrisense/AGRISENSEFULL-STACK/agrisense_app/backend/ml_models"
BACKUP_DIR="/opt/agrisense/backups/ml_models"
TIMESTAMP=$(date +%Y%m%d)

# Create backup
tar -czf "$BACKUP_DIR/ml_models_$TIMESTAMP.tar.gz" -C "$MODELS_DIR" .

# Keep only last 5 backups
ls -t "$BACKUP_DIR"/ml_models_*.tar.gz | tail -n +6 | xargs rm -f

echo "ML models backed up: ml_models_$TIMESTAMP.tar.gz"
```

### Restore Procedures

**Restore PostgreSQL Database**:
```bash
# Stop services
docker-compose down

# Restore from backup
gunzip -c /opt/agrisense/backups/postgres/agrisense_backup_YYYYMMDD_HHMMSS.sql.gz | \
  docker exec -i agrisense-postgres psql -U agrisense -d agrisense_db

# Start services
docker-compose up -d
```

**Restore ML Models**:
```bash
cd /opt/agrisense/AGRISENSEFULL-STACK/agrisense_app/backend
tar -xzf /opt/agrisense/backups/ml_models/ml_models_YYYYMMDD.tar.gz -C ml_models/
docker-compose restart backend
```

---

## SSL/TLS Configuration

### Let's Encrypt with Certbot

**Install Certbot**:
```bash
sudo apt update
sudo apt install certbot python3-certbot-nginx
```

**Obtain Certificate**:
```bash
sudo certbot --nginx -d agrisense.example.com -d www.agrisense.example.com
```

**Auto-Renewal**:
```bash
# Test renewal
sudo certbot renew --dry-run

# Certbot automatically adds cron job at /etc/cron.d/certbot
# Or add manually:
0 0,12 * * * certbot renew --quiet --post-hook "docker-compose restart frontend"
```

### Nginx SSL Configuration

**Create `docker/nginx-ssl.conf`**:
```nginx
server {
    listen 80;
    server_name agrisense.example.com;
    
    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name agrisense.example.com;

    # SSL Certificates
    ssl_certificate /etc/letsencrypt/live/agrisense.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/agrisense.example.com/privkey.pem;

    # SSL Configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers 'ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384';
    ssl_prefer_server_ciphers on;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;
    ssl_stapling on;
    ssl_stapling_verify on;

    # Security Headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # Rest of nginx config...
    include /etc/nginx/conf.d/default.conf;
}
```

**Update `docker-compose.yml`**:
```yaml
frontend:
  volumes:
    - /etc/letsencrypt:/etc/letsencrypt:ro
    - ./docker/nginx-ssl.conf:/etc/nginx/conf.d/default.conf
  ports:
    - "443:443"
    - "80:80"
```

---

## Rate Limiting

### Backend Rate Limiting

**Install slowapi**:
```bash
pip install slowapi
```

**Add to `agrisense_app/backend/main.py`**:
```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address, default_limits=["100/minute"])
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Apply to endpoints
@app.post("/api/disease/detect")
@limiter.limit("10/minute")  # Strict limit for ML endpoints
async def detect_disease(request: Request, ...):
    ...

@app.post("/chatbot/ask")
@limiter.limit("30/minute")  # Moderate limit for chatbot
async def chatbot_ask(request: Request, ...):
    ...
```

### Nginx Rate Limiting

**Update `docker/nginx.conf`**:
```nginx
http {
    # Define rate limit zone
    limit_req_zone $binary_remote_addr zone=api_limit:10m rate=100r/m;
    limit_req_zone $binary_remote_addr zone=ml_limit:10m rate=10r/m;
    
    server {
        # General API rate limit
        location /api/ {
            limit_req zone=api_limit burst=20 nodelay;
            proxy_pass http://backend:8004;
        }
        
        # Stricter limit for ML endpoints
        location ~ ^/api/(disease|weed|crop) {
            limit_req zone=ml_limit burst=5 nodelay;
            proxy_pass http://backend:8004;
        }
    }
}
```

### Load Testing with Locust

**Enhanced `locustfile.py`**:
```python
from locust import HttpUser, task, between

class AgriSenseUser(HttpUser):
    wait_time = between(1, 5)
    
    @task(3)
    def health_check(self):
        self.client.get("/health")
    
    @task(2)
    def chatbot_query(self):
        self.client.post("/chatbot/ask", json={
            "question": "How to grow tomatoes?"
        })
    
    @task(1)
    def crop_recommendation(self):
        self.client.post("/api/crop/recommend", json={
            "nitrogen": 40,
            "phosphorus": 50,
            "potassium": 60,
            "temperature": 25.5,
            "humidity": 65.0,
            "ph": 6.5,
            "rainfall": 200.0
        })
```

**Run Load Test**:
```bash
# Install Locust
pip install locust

# Run with web UI
locust -f locustfile.py --host=http://localhost:8004

# Headless mode
locust -f locustfile.py --host=http://localhost:8004 \
  --users 100 --spawn-rate 10 --run-time 5m --headless \
  --html performance_report.html
```

---

## Security Best Practices

### 1. **Environment Variables**

Never commit secrets to Git. Use `.env` files:

**Create `.env.production`**:
```bash
# Database
DATABASE_URL=postgresql://agrisense:STRONG_PASSWORD@postgres:5432/agrisense_db
POSTGRES_PASSWORD=STRONG_PASSWORD

# Redis
REDIS_URL=redis://redis:6379

# Application
AGRISENSE_ENV=production
AGRISENSE_ADMIN_TOKEN=SECURE_RANDOM_TOKEN
JWT_SECRET_KEY=ANOTHER_SECURE_TOKEN

# External APIs (if any)
WEATHER_API_KEY=your_api_key
```

**Load in docker-compose.yml**:
```yaml
services:
  backend:
    env_file:
      - .env.production
```

### 2. **Security Headers** (already in nginx.conf)

```nginx
add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
add_header X-Frame-Options "SAMEORIGIN" always;
add_header X-Content-Type-Options "nosniff" always;
add_header X-XSS-Protection "1; mode=block" always;
add_header Referrer-Policy "no-referrer-when-downgrade" always;
```

### 3. **Input Validation**

All endpoints use Pydantic models for validation:

```python
from pydantic import BaseModel, Field, validator

class SensorReading(BaseModel):
    temperature: float = Field(..., ge=-50, le=60)
    humidity: float = Field(..., ge=0, le=100)
    
    @validator('temperature')
    def temp_must_be_realistic(cls, v):
        if v < -40 or v > 55:
            raise ValueError('Temperature out of realistic range')
        return v
```

### 4. **CORS Configuration**

Restrict allowed origins in `main.py`:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://agrisense.example.com",
        "https://www.agrisense.example.com",
        # "http://localhost:8082",  # Only for development
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)
```

### 5. **Dependency Updates**

```bash
# Backend
cd AGRISENSEFULL-STACK/agrisense_app/backend
pip-audit
pip install --upgrade -r requirements.txt

# Frontend
cd AGRISENSEFULL-STACK/agrisense_app/frontend/farm-fortune-frontend-main
npm audit fix
npm update
```

### 6. **Container Security**

- ✅ Non-root users in containers
- ✅ Minimal base images (Alpine)
- ✅ Regular vulnerability scans (Trivy, Grype)
- ✅ Read-only filesystem where possible
- ✅ No secrets in images

---

## Troubleshooting

### Common Issues

#### 1. **Container Won't Start**

```bash
# Check logs
docker-compose logs backend
docker-compose logs frontend

# Check container status
docker-compose ps

# Restart services
docker-compose restart backend
```

#### 2. **Database Connection Errors**

```bash
# Check PostgreSQL is running
docker-compose ps postgres

# Test connection
docker exec agrisense-postgres pg_isready -U agrisense

# View PostgreSQL logs
docker-compose logs postgres
```

#### 3. **Port Already in Use**

```bash
# Windows
netstat -ano | findstr :8004
taskkill /PID <PID> /F

# Linux
sudo lsof -i :8004
sudo kill -9 <PID>
```

#### 4. **ML Models Not Loading**

```bash
# Check volume mounts
docker inspect agrisense-backend | grep -A 20 Mounts

# Verify files exist
docker exec agrisense-backend ls -lh backend/ml_models

# Check permissions
docker exec agrisense-backend ls -la backend/ml_models
```

#### 5. **Frontend Not Updating**

```bash
# Clear browser cache
# Hard refresh: Ctrl+Shift+R

# Rebuild frontend image
docker-compose build --no-cache frontend
docker-compose up -d frontend
```

### Health Check Commands

```bash
# Backend
curl -f http://localhost:8004/health
curl -f http://localhost:8004/api/vlm/status

# Frontend
curl -f http://localhost:80/health

# PostgreSQL
docker exec agrisense-postgres pg_isready -U agrisense

# Redis
docker exec agrisense-redis redis-cli ping

# All services
docker-compose ps
```

### Performance Debugging

```bash
# Container resource usage
docker stats

# Check disk space
docker system df

# Clean up unused resources
docker system prune -a
docker volume prune
```

---

## Additional Resources

- **Backend API Docs**: http://localhost:8004/docs
- **Prometheus Metrics**: http://localhost:8004/metrics
- **Grafana Dashboards**: http://localhost:3000
- **GitHub Actions**: https://github.com/your-org/agrisense/actions

---

**Document Version**: 1.0.0  
**Last Updated**: January 2025  
**Maintained By**: AgriSense DevOps Team  
**Status**: Production Ready ✅
