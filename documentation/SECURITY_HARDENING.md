"""
Security Hardening Guide for AgriSense
========================================

This document provides comprehensive security hardening guidelines for deploying
and operating AgriSense in production environments.

## 1. HTTPS/TLS Configuration

### Setting Up HTTPS with Let's Encrypt

#### Option 1: Nginx Reverse Proxy with Auto-SSL

```nginx
# /etc/nginx/sites-available/agrisense
server {
    listen 80;
    server_name yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com;

    # SSL certificates from Let's Encrypt
    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;

    # SSL configuration (Mozilla Intermediate)
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_prefer_server_ciphers off;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384;

    # OCSP stapling
    ssl_stapling on;
    ssl_stapling_verify on;
    ssl_trusted_certificate /etc/letsencrypt/live/yourdomain.com/chain.pem;

    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; font-src 'self' data:; connect-src 'self' https://api.openai.com https://generativelanguage.googleapis.com;" always;
    add_header Permissions-Policy "geolocation=(), microphone=(), camera=()" always;

    location / {
        proxy_pass http://127.0.0.1:8004;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
        
        # Timeout settings
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
}
```

#### Auto-renewal with Certbot

```bash
# Install certbot
sudo apt-get update
sudo apt-get install certbot python3-certbot-nginx

# Get certificate
sudo certbot --nginx -d yourdomain.com

# Auto-renewal (runs twice daily)
sudo systemctl enable certbot.timer
sudo systemctl start certbot.timer
```

#### Option 2: Uvicorn with SSL

```bash
# Generate self-signed cert (for testing only)
openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 365 -nodes

# Run with SSL
uvicorn agrisense_app.backend.main:app \\
    --host 0.0.0.0 \\
    --port 8443 \\
    --ssl-keyfile key.pem \\
    --ssl-certfile cert.pem
```

## 2. Security Headers Implementation

Add to FastAPI middleware:

```python
# agrisense_app/backend/middleware/security_headers.py
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # HSTS - Force HTTPS
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        
        # Prevent clickjacking
        response.headers["X-Frame-Options"] = "SAMEORIGIN"
        
        # Prevent MIME sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"
        
        # XSS Protection
        response.headers["X-XSS-Protection"] = "1; mode=block"
        
        # Referrer Policy
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        # Content Security Policy
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self' data:; "
            "connect-src 'self' https://api.openai.com https://generativelanguage.googleapis.com;"
        )
        
        # Permissions Policy
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        
        return response
```

## 3. Secrets Management

### Environment Variables (Production)

```bash
# .env.production (NEVER commit this file)
# Use a secret management system in production

# Database
DATABASE_URL=postgresql://user:SECURE_PASSWORD@localhost/agrisense
REDIS_URL=redis://:SECURE_PASSWORD@localhost:6379/0

# JWT Secret (generate with: openssl rand -hex 32)
AGRISENSE_JWT_SECRET=your_64_char_hex_secret_here

# Admin Token (generate with: openssl rand -hex 32)
AGRISENSE_ADMIN_TOKEN=your_64_char_admin_token_here

# API Keys (rotate every 90 days)
OPENAI_API_KEY=sk-...
GOOGLE_API_KEY=AI...

# SMTP (for alerts)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=alerts@yourdomain.com
SMTP_PASSWORD=app_specific_password

# Sentry
SENTRY_DSN=https://...@sentry.io/...
SENTRY_ENVIRONMENT=production

# CORS
ALLOWED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
```

### Secrets Rotation Schedule

| Secret | Rotation Period | Auto-Rotate |
|--------|----------------|-------------|
| JWT Secret | 90 days | No |
| Admin Token | 90 days | No |
| API Keys | 90 days | Yes (via API) |
| Database Password | 180 days | No |
| SMTP Password | 180 days | No |
| SSL Certificates | 90 days | Yes (Certbot) |

### Using HashiCorp Vault (Recommended for Production)

```python
# agrisense_app/backend/config/vault_config.py
import hvac
import os

def get_vault_client():
    client = hvac.Client(
        url=os.getenv('VAULT_ADDR', 'https://vault.yourdomain.com'),
        token=os.getenv('VAULT_TOKEN')
    )
    return client

def get_secret(path: str, key: str):
    client = get_vault_client()
    secret = client.secrets.kv.v2.read_secret_version(path=path)
    return secret['data']['data'][key]

# Usage
AGRISENSE_JWT_SECRET = get_secret('agrisense/prod', 'jwt_secret')
```

## 4. Database Security

### PostgreSQL Hardening

```sql
-- Create restricted user
CREATE USER agrisense_app WITH PASSWORD 'SECURE_PASSWORD';

-- Grant minimal permissions
GRANT CONNECT ON DATABASE agrisense TO agrisense_app;
GRANT USAGE ON SCHEMA public TO agrisense_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO agrisense_app;
GRANT USAGE ON ALL SEQUENCES IN SCHEMA public TO agrisense_app;

-- Enable SSL
ALTER SYSTEM SET ssl = 'on';
ALTER SYSTEM SET ssl_cert_file = '/path/to/server.crt';
ALTER SYSTEM SET ssl_key_file = '/path/to/server.key';

-- Restrict connections
-- Edit pg_hba.conf:
hostssl    agrisense    agrisense_app    10.0.0.0/8    md5
```

### MongoDB Security

```javascript
// Create user with minimal permissions
use agrisense
db.createUser({
  user: "agrisense_app",
  pwd: "SECURE_PASSWORD",
  roles: [
    { role: "readWrite", db: "agrisense" }
  ]
})

// Enable authentication in mongod.conf
security:
  authorization: enabled
```

## 5. API Rate Limiting

Enhanced rate limiting configuration:

```python
# agrisense_app/backend/config/rate_limits.py
RATE_LIMITS = {
    "/api/*": {
        "requests": 100,
        "window": 60,  # 100 requests per minute
    },
    "/chatbot/ask": {
        "requests": 20,
        "window": 60,  # 20 requests per minute
    },
    "/recommend": {
        "requests": 30,
        "window": 60,
    },
    "/api/disease/detect": {
        "requests": 10,
        "window": 60,  # 10 image analyses per minute
    },
    "/ingest": {
        "requests": 200,
        "window": 60,  # 200 sensor readings per minute
    },
    "default": {
        "requests": 60,
        "window": 60,
    },
}
```

## 6. Input Validation

Always validate and sanitize inputs:

```python
from pydantic import BaseModel, Field, validator

class SensorReading(BaseModel):
    zone_id: str = Field(..., max_length=50, regex=r'^[a-zA-Z0-9_-]+$')
    ph: float = Field(..., ge=0, le=14)
    moisture_pct: float = Field(..., ge=0, le=100)
    temperature_c: float = Field(..., ge=-50, le=60)
    
    @validator('zone_id')
    def sanitize_zone_id(cls, v):
        # Remove any potentially dangerous characters
        return v.strip()
```

## 7. Authentication & Authorization

### JWT Token Security

```python
# Secure JWT configuration
JWT_SECRET_KEY = os.getenv("AGRISENSE_JWT_SECRET")
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_MINUTES = 60  # Short-lived tokens
JWT_REFRESH_EXPIRATION_DAYS = 7

# Token rotation
def create_tokens(user_id: str):
    access_token = create_access_token(user_id, expires_delta=timedelta(minutes=60))
    refresh_token = create_refresh_token(user_id, expires_delta=timedelta(days=7))
    return {"access_token": access_token, "refresh_token": refresh_token}
```

### Role-Based Access Control (RBAC)

```python
from enum import Enum

class Role(str, Enum):
    ADMIN = "admin"
    FARMER = "farmer"
    VIEWER = "viewer"
    IOT_DEVICE = "iot_device"

def require_role(required_role: Role):
    def decorator(func):
        async def wrapper(*args, current_user: User = Depends(get_current_user), **kwargs):
            if current_user.role != required_role:
                raise HTTPException(status_code=403, detail="Insufficient permissions")
            return await func(*args, current_user=current_user, **kwargs)
        return wrapper
    return decorator

# Usage
@app.post("/admin/reset")
@require_role(Role.ADMIN)
async def admin_reset(current_user: User):
    ...
```

## 8. Logging & Monitoring

### Secure Logging Configuration

```python
import logging
from logging.handlers import RotatingFileHandler
import os

# Never log sensitive data
SENSITIVE_FIELDS = ['password', 'token', 'api_key', 'secret']

class SecureFormatter(logging.Formatter):
    def format(self, record):
        # Redact sensitive fields
        if hasattr(record, 'args'):
            record.args = tuple(
                '***REDACTED***' if any(field in str(arg).lower() for field in SENSITIVE_FIELDS)
                else arg
                for arg in record.args
            )
        return super().format(record)

# Configure logging
handler = RotatingFileHandler(
    'logs/agrisense.log',
    maxBytes=10485760,  # 10MB
    backupCount=10
)
handler.setFormatter(SecureFormatter(
    '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
))
```

## 9. Firewall Configuration

### UFW (Ubuntu)

```bash
# Allow SSH
sudo ufw allow 22/tcp

# Allow HTTPS only
sudo ufw allow 443/tcp

# Allow from specific IPs only (for IoT devices)
sudo ufw allow from 192.168.1.0/24 to any port 8004

# Enable firewall
sudo ufw enable
```

## 10. Security Checklist for Production

### Pre-Deployment
- [ ] All dependencies updated to latest secure versions
- [ ] Security audit completed (pip-audit, npm audit)
- [ ] No hardcoded secrets in code
- [ ] Environment variables configured
- [ ] SSL/TLS certificates installed
- [ ] Security headers configured
- [ ] Rate limiting enabled
- [ ] Input validation on all endpoints
- [ ] CORS properly configured

### Post-Deployment
- [ ] Sentry error tracking active
- [ ] Log monitoring configured
- [ ] Backup system in place
- [ ] Secrets rotation schedule documented
- [ ] Security audit scheduled (quarterly)
- [ ] Penetration testing completed
- [ ] Incident response plan documented

### Ongoing Maintenance
- [ ] Weekly: Review error logs
- [ ] Monthly: Security patch updates
- [ ] Quarterly: Secrets rotation
- [ ] Quarterly: Security audit
- [ ] Annually: Penetration testing
- [ ] Annually: SSL certificate renewal (if not auto-renewed)

## 11. Incident Response Plan

### Security Incident Categories

1. **Critical**: Data breach, unauthorized access, service compromise
2. **High**: DDoS attack, attempted intrusion, data exposure
3. **Medium**: Suspicious activity, failed login attempts
4. **Low**: Configuration issues, outdated dependencies

### Response Procedures

1. **Detect**: Monitor logs, alerts, error rates
2. **Contain**: Isolate affected systems, disable compromised accounts
3. **Investigate**: Review logs, identify root cause
4. **Remediate**: Apply patches, rotate secrets, update configurations
5. **Recover**: Restore from backups if needed, verify system integrity
6. **Document**: Post-mortem report, lessons learned

### Emergency Contacts

```yaml
security_team:
  lead: security@yourdomain.com
  on_call: +1-XXX-XXX-XXXX

escalation:
  level_1: DevOps team
  level_2: Security team
  level_3: CTO/CISO

external:
  hosting: support@cloudprovider.com
  security_firm: security@consultant.com
```

## 12. Compliance Considerations

### GDPR (if applicable)
- User data encryption at rest and in transit
- Right to deletion implementation
- Data processing agreements
- Privacy policy

### Data Retention
- Sensor data: 2 years
- User data: Until account deletion
- Logs: 90 days
- Backups: 30 days

---

Last Updated: 2025-10-01
Review Schedule: Quarterly
