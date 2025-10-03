# AgriSense Production Deployment Guide

## Overview

This guide covers the complete production deployment of the AgriSense platform with all upgraded components including React 19, PostgreSQL, Redis, Celery background tasks, monitoring stack, and Kubernetes orchestration.

## Architecture Summary

### Frontend Stack
- **React 19** with TanStack Query v5 for state management
- **Vite** optimized build with code splitting and lazy loading
- **Framer Motion** for animations and user experience
- **Enhanced PWA v2** with offline capabilities and push notifications
- **Responsive Design** with accessibility compliance
- **Advanced Data Visualization** using Recharts and TypeScript

### Backend Stack
- **FastAPI** with async/await patterns and high performance
- **PostgreSQL** with asyncpg driver and connection pooling
- **Redis** for caching, session storage, and Celery broker
- **JWT Authentication** with fastapi-users and role-based access
- **Rate Limiting** with slowapi and Redis backend
- **TensorFlow Serving** for ML model inference
- **WebSocket** real-time communication

### Background Processing
- **Celery** with Redis broker and specialized task queues
- **Task Queues**: data_processing, reports, ml_inference, notifications, scheduled
- **Beat Scheduler** for periodic tasks and maintenance
- **Flower** monitoring dashboard for task management
- **Comprehensive API** for task submission and monitoring

### Infrastructure & Monitoring
- **Kubernetes** deployment with blue-green strategy
- **Docker** multi-stage builds for optimization
- **Prometheus** metrics collection with custom metrics
- **Grafana** dashboards for visualization and alerting
- **Alertmanager** for notification routing
- **GitHub Actions** CI/CD pipeline with security scanning

## Deployment Process

### Prerequisites

1. **Kubernetes Cluster** (1.25+)
2. **Docker Registry** (GitHub Container Registry recommended)
3. **kubectl** and **helm** CLI tools
4. **Domain** with SSL certificates
5. **External Services**: PostgreSQL, Redis (or deploy with provided manifests)

### Environment Setup

1. **Copy Environment Configuration**
   ```bash
   cp .env.production.example .env.production
   ```

2. **Update Configuration Values**
   - Database connection strings
   - JWT secret keys
   - API keys (OpenWeather, SMS, etc.)
   - SMTP configuration
   - Monitoring credentials

3. **Create Kubernetes Secrets**
   ```bash
   kubectl create secret generic agrisense-secrets \
     --from-env-file=.env.production \
     --namespace=agrisense-production
   ```

### Deployment Steps

#### Option 1: Automated Deployment (Recommended)

```bash
# Make deployment script executable
chmod +x scripts/deploy.sh

# Deploy to production
./scripts/deploy.sh --env production --tag latest

# Deploy to staging for testing
./scripts/deploy.sh --env staging --tag develop
```

#### Option 2: Manual Deployment

1. **Build and Push Images**
   ```bash
   # Build main application
   docker build -t ghcr.io/your-org/agrisense:latest .
   docker push ghcr.io/your-org/agrisense:latest
   
   # Build Celery workers
   docker build -f Dockerfile.celery -t ghcr.io/your-org/agrisense-celery:latest .
   docker push ghcr.io/your-org/agrisense-celery:latest
   ```

2. **Deploy Infrastructure**
   ```bash
   # Create namespace
   kubectl create namespace agrisense-production
   
   # Deploy application
   kubectl apply -f k8s/production.yaml
   
   # Deploy monitoring (optional)
   kubectl apply -f k8s/monitoring.yaml
   ```

3. **Run Database Migrations**
   ```bash
   kubectl create job agrisense-migration \
     --image=ghcr.io/your-org/agrisense:latest \
     --namespace=agrisense-production \
     -- python -m alembic upgrade head
   ```

### Service Configuration

#### Main Services

| Service | Port | Description | Health Check |
|---------|------|-------------|--------------|
| Backend API | 8004 | Main FastAPI application | `/health` |
| Celery Workers | - | Background task processing | Flower dashboard |
| Redis | 6379 | Cache and message broker | `redis-cli ping` |
| Flower | 5555 | Celery monitoring | `/flower` |
| Prometheus | 9090 | Metrics collection | `/metrics` |
| Grafana | 3000 | Monitoring dashboards | `/api/health` |

#### Ingress Configuration

```yaml
# Production ingress with SSL
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: agrisense-ingress
  annotations:
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
spec:
  tls:
  - hosts:
    - agrisense.com
    secretName: agrisense-tls
  rules:
  - host: agrisense.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: agrisense-backend-service
            port:
              number: 80
```

### Monitoring & Alerting

#### Prometheus Metrics

- **Application Metrics**: Request duration, error rates, active users
- **Infrastructure Metrics**: CPU, memory, disk usage
- **Business Metrics**: Sensor readings, recommendations, user activity
- **Celery Metrics**: Task execution time, queue lengths, worker status

#### Grafana Dashboards

1. **Overview Dashboard**: System health, active users, key metrics
2. **Business Dashboard**: Irrigation recommendations, crop insights, cost savings
3. **System Dashboard**: Infrastructure metrics, performance indicators
4. **Celery Dashboard**: Task queues, worker performance, error rates

#### Alert Rules

- **High Error Rate**: > 5% error rate for 5 minutes
- **High Response Time**: > 2s average response time for 10 minutes
- **Low Disk Space**: < 10% free disk space
- **Failed Tasks**: > 10 failed Celery tasks in 5 minutes
- **Service Down**: Service unavailable for 2 minutes

### Security Configuration

#### Authentication & Authorization

- **JWT Tokens**: Access tokens expire in 30 minutes
- **Refresh Tokens**: Expire in 7 days with automatic rotation
- **Role-Based Access**: Admin, Farmer, Observer roles
- **API Rate Limiting**: 100 requests per minute per IP

#### Network Security

- **Network Policies**: Restrict pod-to-pod communication
- **SSL/TLS**: All external traffic encrypted
- **Secret Management**: Kubernetes secrets for sensitive data
- **Container Security**: Non-root user, minimal base images

#### Security Scanning

- **Trivy**: Container vulnerability scanning
- **Bandit**: Python security linting
- **Safety**: Python dependency vulnerability check
- **npm audit**: Node.js dependency security audit

### Performance Optimization

#### Horizontal Pod Autoscaling

```yaml
# Backend HPA
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: agrisense-backend-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: agrisense-backend-blue
  minReplicas: 3
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
```

#### Database Optimization

- **Connection Pooling**: 20 connections per pod
- **Query Optimization**: Proper indexing and query analysis
- **Read Replicas**: For analytics and reporting workloads
- **Backup Strategy**: Daily automated backups with 30-day retention

#### Caching Strategy

- **Redis Caching**: API responses, session data, rate limiting
- **CDN**: Static assets and frontend distribution
- **Application Caching**: ML model predictions, weather data
- **Database Query Caching**: Frequently accessed data

### Backup & Recovery

#### Database Backup

```bash
# Automated daily backup job
apiVersion: batch/v1
kind: CronJob
metadata:
  name: database-backup
spec:
  schedule: "0 2 * * *"  # Daily at 2 AM
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: backup
            image: postgres:15
            command:
            - /bin/bash
            - -c
            - pg_dump $DATABASE_URL | gzip > /backup/backup-$(date +%Y%m%d).sql.gz
```

#### Disaster Recovery

1. **Data Recovery**: Automated database backups with point-in-time recovery
2. **Application Recovery**: Blue-green deployment for zero-downtime rollback
3. **Infrastructure Recovery**: Infrastructure as Code with Kubernetes manifests
4. **Monitoring Recovery**: Prometheus data retention and Grafana configuration backup

### Troubleshooting

#### Common Issues

1. **Pod Startup Failures**
   ```bash
   kubectl describe pod <pod-name> -n agrisense-production
   kubectl logs <pod-name> -n agrisense-production
   ```

2. **Database Connection Issues**
   ```bash
   kubectl exec -it <backend-pod> -n agrisense-production -- python -c "import asyncpg; print('OK')"
   ```

3. **Celery Task Failures**
   ```bash
   kubectl port-forward service/flower-service 5555:5555 -n agrisense-production
   # Open http://localhost:5555 for task monitoring
   ```

4. **Performance Issues**
   ```bash
   kubectl top pods -n agrisense-production
   kubectl top nodes
   ```

#### Log Analysis

```bash
# Application logs
kubectl logs deployment/agrisense-backend-blue -n agrisense-production --tail=100

# Celery worker logs
kubectl logs deployment/celery-worker-data -n agrisense-production --tail=100

# System logs
kubectl get events -n agrisense-production --sort-by='.lastTimestamp'
```

### Maintenance

#### Regular Tasks

1. **Weekly**: Review monitoring alerts and performance metrics
2. **Monthly**: Update dependencies and security patches
3. **Quarterly**: Review and update backup retention policies
4. **Annually**: Security audit and penetration testing

#### Scaling Guidelines

- **CPU Usage > 70%**: Scale up backend pods
- **Memory Usage > 80%**: Increase pod memory limits
- **Queue Length > 100**: Scale up Celery workers
- **Response Time > 2s**: Review database queries and caching

### Support & Documentation

#### API Documentation

- **Swagger UI**: Available at `/docs` endpoint
- **ReDoc**: Available at `/redoc` endpoint
- **OpenAPI Spec**: Available at `/openapi.json`

#### Monitoring URLs

- **Main Application**: https://agrisense.com
- **API Health**: https://agrisense.com/health
- **Metrics**: https://agrisense.com/metrics (admin only)
- **Grafana**: https://monitoring.agrisense.com
- **Flower**: https://agrisense.com/flower (admin only)

---

For additional support or questions, please refer to the project documentation or contact the development team.