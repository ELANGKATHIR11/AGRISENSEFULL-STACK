





















































































































# 🚀 AgriSense - Quick Start Deployment

**Last Updated**: January 2025  
**Estimated Time**: 15 minutes  
**Difficulty**: Beginner-Friendly

---

## ⚡ TL;DR - Deploy in 5 Commands

```bash
# 1. Clone and navigate
cd AGRISENSEFULL-STACK

# 2. Set environment variables
export POSTGRES_PASSWORD="your-secure-password-here"

# 3. Start all services
docker-compose up -d

# 4. Wait for services to be ready (60 seconds)
sleep 60

# 5. Verify deployment
curl http://localhost:8004/health
curl http://localhost:80/health
```

**✅ Done!** Your AgriSense platform is now running:
- Frontend: http://localhost:80
- Backend API: http://localhost:8004
- API Docs: http://localhost:8004/docs
- Database: PostgreSQL on port 5432
- Cache: Redis on port 6379

---

## 📋 Prerequisites Checklist

### Required Software
- [ ] **Docker** 24.0+ installed ([Install Docker](https://docs.docker.com/get-docker/))
- [ ] **Docker Compose** 2.20+ installed (usually comes with Docker)
- [ ] **Git** (to clone the repository)

### Verify Installation
```powershell
# Check Docker
docker --version
# Should show: Docker version 24.0.x or higher

# Check Docker Compose
docker-compose --version
# Should show: Docker Compose version 2.20.x or higher

# Check if Docker is running
docker ps
# Should show empty list or running containers (no errors)
```

---

## 🎯 Step-by-Step Deployment

### Step 1: Prepare Environment (2 minutes)

**Windows (PowerShell)**:
```powershell
# Navigate to project
cd "D:\AGRISENSE FULL-STACK\AGRISENSEFULL-STACK"

# Set environment variables
$env:POSTGRES_PASSWORD = "MySecurePassword123!"
$env:AGRISENSE_ADMIN_TOKEN = "AdminToken456!"
$env:AGRISENSE_ENV = "production"
```

**Linux/Mac (Bash)**:
```bash
# Navigate to project
cd /path/to/AGRISENSEFULL-STACK

# Set environment variables
export POSTGRES_PASSWORD="MySecurePassword123!"
export AGRISENSE_ADMIN_TOKEN="AdminToken456!"
export AGRISENSE_ENV="production"

# Or create .env file
cat > .env.production << EOF
POSTGRES_PASSWORD=MySecurePassword123!
AGRISENSE_ADMIN_TOKEN=AdminToken456!
AGRISENSE_ENV=production
DATABASE_URL=postgresql://agrisense:\${POSTGRES_PASSWORD}@postgres:5432/agrisense_db
REDIS_URL=redis://redis:6379
AGRISENSE_DISABLE_ML=0
EOF
```

### Step 2: Start Services (1 minute)

```bash
# Start all containers in detached mode
docker-compose up -d

# Expected output:
# Creating network "agrisensefull-stack_agrisense-network" ... done
# Creating volume "agrisensefull-stack_postgres_data" ... done
# Creating volume "agrisensefull-stack_redis_data" ... done
# Creating agrisense-postgres ... done
# Creating agrisense-redis ... done
# Creating agrisense-backend ... done
# Creating agrisense-frontend ... done
```

### Step 3: Monitor Startup (2 minutes)

```bash
# Watch logs in real-time
docker-compose logs -f

# Or check specific service
docker-compose logs -f backend

# Wait for these messages:
# backend    | INFO:     Uvicorn running on http://0.0.0.0:8004
# postgres   | database system is ready to accept connections
# redis      | Ready to accept connections
# frontend   | /docker-entrypoint.sh: Configuration complete; ready for start up
```

**Press `Ctrl+C` to stop watching logs** (services keep running).

### Step 4: Verify Deployment (1 minute)

**Check Container Status**:
```bash
docker-compose ps

# Expected output (all should be "Up"):
# NAME                  STATUS
# agrisense-backend     Up (healthy)
# agrisense-frontend    Up (healthy)
# agrisense-postgres    Up (healthy)
# agrisense-redis       Up (healthy)
```

**Health Checks**:
```bash
# Backend health
curl http://localhost:8004/health
# Expected: {"status":"healthy"}

# Frontend health
curl http://localhost:80/health
# Expected: healthy

# VLM status
curl http://localhost:8004/api/vlm/status
# Expected: {"vlm_available":true/false,...}
```

### Step 5: Access Application (1 minute)

**Open in Browser**:
- **Frontend**: http://localhost:80
- **Backend API Docs**: http://localhost:8004/docs
- **Backend Redoc**: http://localhost:8004/redoc

**Test Features**:
1. Navigate to Dashboard
2. Switch languages (English → Hindi → Tamil)
3. Try Chatbot: "How to grow tomatoes?"
4. Check Crop Recommendation page
5. View Disease Detection page

---

## 🎛️ Common Operations

### View Logs
```bash
# All services
docker-compose logs

# Specific service
docker-compose logs backend
docker-compose logs frontend
docker-compose logs postgres
docker-compose logs redis

# Follow logs in real-time
docker-compose logs -f backend

# Last 50 lines
docker-compose logs --tail=50 backend
```

### Restart Services
```bash
# Restart all
docker-compose restart

# Restart specific service
docker-compose restart backend
docker-compose restart frontend
```

### Stop Services
```bash
# Stop all (keeps volumes)
docker-compose stop

# Stop and remove containers (keeps volumes)
docker-compose down

# Stop, remove containers AND volumes (deletes data!)
docker-compose down -v
```

### Update Application
```bash
# Pull latest code
git pull origin main

# Rebuild images
docker-compose build

# Restart with new images
docker-compose up -d

# Or do it all at once
docker-compose up -d --build
```

### Scale Services
```bash
# Run 4 backend workers
docker-compose up -d --scale backend=4

# Note: Only works if you remove the container_name directive
```

---

## 🐛 Troubleshooting

### Issue 1: Port Already in Use

**Symptom**:
```
Error: bind: address already in use
```

**Solution**:

**Windows**:
```powershell
# Find process using port 8004
netstat -ano | findstr :8004

# Kill process (replace PID with actual number)
taskkill /PID <PID> /F

# Or change port in docker-compose.yml:
# ports:
#   - "8005:8004"  # Use 8005 instead
```

**Linux/Mac**:
```bash
# Find and kill process
sudo lsof -i :8004
sudo kill -9 <PID>

# Or change port in docker-compose.yml
```

### Issue 2: Container Fails to Start

**Symptom**:
```
Container exited with code 1
```

**Solution**:
```bash
# Check logs for errors
docker-compose logs backend

# Common fixes:
# 1. Missing environment variables
echo $POSTGRES_PASSWORD  # Should show your password

# 2. Database not ready yet
docker-compose restart backend  # Retry after DB is ready

# 3. Volume permission issues
sudo chown -R $USER:$USER ./volumes/
```

### Issue 3: Database Connection Error

**Symptom**:
```
could not connect to server: Connection refused
```

**Solution**:
```bash
# Check if PostgreSQL is running
docker-compose ps postgres

# Check PostgreSQL logs
docker-compose logs postgres

# Verify connection
docker exec agrisense-postgres pg_isready -U agrisense

# Restart database
docker-compose restart postgres
```

### Issue 4: Frontend Shows White Page

**Symptom**: Browser loads but shows blank white page

**Solution**:
```bash
# 1. Hard refresh browser
# Press: Ctrl + Shift + R (Windows)
# Press: Cmd + Shift + R (Mac)

# 2. Check frontend logs
docker-compose logs frontend

# 3. Rebuild frontend
docker-compose build frontend
docker-compose up -d frontend

# 4. Clear browser cache
# Chrome: Settings → Privacy → Clear browsing data
```

### Issue 5: Slow Performance

**Symptom**: API responses take >5 seconds

**Solution**:
```bash
# 1. Check resource usage
docker stats

# 2. If CPU > 90% or Memory > 80%:
# Increase Docker resources:
# Docker Desktop → Settings → Resources
# Set: CPUs: 4+, Memory: 8GB+

# 3. Disable ML if not needed
# In docker-compose.yml:
#   environment:
#     - AGRISENSE_DISABLE_ML=1

# 4. Restart services
docker-compose restart
```

---

## 🔧 Configuration Options

### Disable ML Models (Faster Startup)

Edit `docker-compose.yml`:
```yaml
backend:
  environment:
    - AGRISENSE_DISABLE_ML=1  # Add this line
```

Restart: `docker-compose up -d`

### Change Ports

Edit `docker-compose.yml`:
```yaml
backend:
  ports:
    - "8005:8004"  # Changed from 8004:8004

frontend:
  ports:
    - "8080:80"    # Changed from 80:80
```

Restart: `docker-compose up -d`

### Enable Debug Logging

Edit `docker-compose.yml`:
```yaml
backend:
  environment:
    - LOG_LEVEL=DEBUG  # Add this line
```

Restart: `docker-compose up -d`

### Custom Database Password

**Option 1: Environment Variable**:
```bash
export POSTGRES_PASSWORD="MyNewPassword"
docker-compose up -d
```

**Option 2: .env File**:
```bash
# Create .env.production
echo "POSTGRES_PASSWORD=MyNewPassword" > .env.production

# Load in docker-compose.yml
docker-compose --env-file .env.production up -d
```

---

## 📊 Monitoring Commands

### Check Resource Usage
```bash
# Real-time stats
docker stats

# Disk usage
docker system df

# Network activity
docker network inspect agrisensefull-stack_agrisense-network
```

### Database Queries
```bash
# Connect to PostgreSQL
docker exec -it agrisense-postgres psql -U agrisense -d agrisense_db

# Inside psql:
# List tables
\dt

# Count sensor readings
SELECT COUNT(*) FROM sensor_readings;

# Latest readings
SELECT * FROM sensor_readings ORDER BY timestamp DESC LIMIT 10;

# Exit
\q
```

### Redis Cache
```bash
# Connect to Redis
docker exec -it agrisense-redis redis-cli

# Inside redis-cli:
# Show all keys
KEYS *

# Get cache stats
INFO stats

# Exit
exit
```

---

## 🛑 Uninstall / Clean Up

### Stop and Remove Everything
```bash
# Stop containers
docker-compose down

# Remove volumes (deletes all data!)
docker-compose down -v

# Remove images
docker rmi $(docker images 'agrisense*' -q)

# Remove all unused Docker resources
docker system prune -a --volumes
```

**⚠️ Warning**: This deletes ALL data including database records!

---

## 🎓 Next Steps

After successful deployment:

1. **🔒 Secure Your Installation**:
   - Change default passwords
   - Enable SSL/TLS (see `PRODUCTION_DEPLOYMENT_GUIDE.md`)
   - Set up firewall rules

2. **📊 Set Up Monitoring**:
   - Configure Prometheus + Grafana
   - Set up alerting rules
   - See "Monitoring & Alerting" section in main guide

3. **🧪 Run Tests**:
   ```bash
   # Install Playwright
   npm install
   npx playwright install
   
   # Run E2E tests
   npm test
   ```

4. **📱 Access from Other Devices**:
   - Find your server IP: `ipconfig` (Windows) or `ifconfig` (Linux/Mac)
   - Access from phone/tablet: `http://YOUR_IP:80`
   - Configure firewall to allow ports 80, 8004

5. **☁️ Deploy to Cloud**:
   - See `PRODUCTION_DEPLOYMENT_GUIDE.md` for AWS/Azure/GCP instructions
   - Set up CI/CD pipeline with GitHub Actions
   - Configure domain name and SSL certificates

---

## 📚 Additional Resources

- **Full Deployment Guide**: `PRODUCTION_DEPLOYMENT_GUIDE.md`
- **E2E Testing**: `E2E_TESTING_GUIDE.md`
- **Implementation Summary**: `PRODUCTION_DEPLOYMENT_IMPLEMENTATION_SUMMARY.md`
- **Backend API Docs**: http://localhost:8004/docs (after deployment)
- **Architecture Blueprint**: `PROJECT_BLUEPRINT_UPDATED.md`

---

## 🆘 Get Help

**Check Logs First**:
```bash
docker-compose logs -f
```

**Common Log Locations**:
- Backend logs: `docker-compose logs backend`
- PostgreSQL logs: `docker-compose logs postgres`
- Nginx logs: `docker-compose logs frontend`

**Still Having Issues?**
1. Check the troubleshooting section above
2. Review `PRODUCTION_DEPLOYMENT_GUIDE.md`
3. Search for error message in project documentation
4. Check GitHub Issues (if repository is public)

---

## ✅ Success Checklist

- [ ] All 4 containers running (`docker-compose ps`)
- [ ] Backend health check passes (`curl http://localhost:8004/health`)
- [ ] Frontend health check passes (`curl http://localhost:80/health`)
- [ ] Frontend accessible in browser (`http://localhost:80`)
- [ ] API docs accessible (`http://localhost:8004/docs`)
- [ ] Database accepting connections
- [ ] Redis cache operational
- [ ] Can navigate between pages
- [ ] Chatbot responds to questions
- [ ] Language switcher works

**✅ All checks passed?** Congratulations! Your AgriSense platform is live! 🎉

---

**Document Version**: 1.0.0  
**Last Updated**: January 2025  
**Estimated Total Time**: 15 minutes  
**Difficulty**: ⭐⭐☆☆☆ (Easy)
