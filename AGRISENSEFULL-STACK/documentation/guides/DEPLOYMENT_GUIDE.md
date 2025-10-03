# AgriSense Deployment Guide

## 🚀 **Quick Start**

### **1. Start the Server**
```bash
cd agrisense_app/backend
python -m uvicorn main:app --host 0.0.0.0 --port 8004 --reload
```

### **2. Access the Application**
- **Web Interface**: http://localhost:8004/ui
- **API Documentation**: http://localhost:8004/docs
- **Health Check**: http://localhost:8004/health

---

## 📋 **Prerequisites**

### **System Requirements**
- **Python**: 3.9 or higher
- **Node.js**: 16 or higher (for frontend development)
- **Memory**: 4GB RAM minimum
- **Storage**: 2GB free space

### **Python Dependencies**
```bash
cd agrisense_app/backend
pip install -r requirements.txt
```

### **Frontend Dependencies** (Development Only)
```bash
cd agrisense_app/frontend/farm-fortune-frontend-main
npm install
npm run build
```

---

## 🔧 **Configuration**

### **Environment Variables**
Create a `.env` file in the backend directory:

```env
# Database Configuration
AGRISENSE_DB=sqlite
DATABASE_URL=sqlite:///./sensors.db

# Security
AGRISENSE_ADMIN_TOKEN=your-secure-admin-token-here

# CORS Settings
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8004

# Optional: External Services
SMTP_PASSWORD=your-smtp-password
AGRISENSE_TWILIO_TOKEN=your-twilio-token
```

### **Database Setup**
The system uses SQLite by default. No additional setup required.

For MongoDB (optional):
```env
AGRISENSE_DB=mongodb
DATABASE_URL=mongodb://localhost:27017/agrisense
```

---

## 🌐 **Production Deployment**

### **Option 1: Direct Server Deployment**

1. **Install Dependencies**
   ```bash
   cd agrisense_app/backend
   pip install -r requirements.txt
   ```

2. **Build Frontend**
   ```bash
   cd agrisense_app/frontend/farm-fortune-frontend-main
   npm run build
   ```

3. **Start Production Server**
   ```bash
   cd agrisense_app/backend
   python -m uvicorn main:app --host 0.0.0.0 --port 8004
   ```

### **Option 2: Docker Deployment**

Create `Dockerfile`:
```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY agrisense_app/backend/ .
RUN pip install -r requirements.txt

EXPOSE 8004
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8004"]
```

Build and run:
```bash
docker build -t agrisense .
docker run -p 8004:8004 agrisense
```

### **Option 3: Cloud Deployment**

For cloud platforms (AWS, GCP, Azure):
1. Use the provided `start_agrisense.py` script
2. Configure environment variables for your cloud provider
3. Set up load balancer for port 8004
4. Configure SSL/TLS certificates

---

## 🔍 **Health Monitoring**

### **Health Check Endpoints**
- **Basic Health**: `GET /health`
- **Detailed Health**: `GET /health/enhanced`
- **Readiness**: `GET /ready`
- **Live Status**: `GET /live`

### **System Status**
```bash
curl http://localhost:8004/health
```

Expected response:
```json
{
  "status": "ok",
  "timestamp": 1695475200.123
}
```

---

## 🧪 **Testing the Deployment**

### **1. Run Backend Tests**
```bash
cd scripts
python test_backend_clean.py
```

### **2. Run VLM Integration Tests**
```bash
cd scripts
python test_vlm_integration_clean.py
```

### **3. Manual Testing**
1. Open http://localhost:8004/ui
2. Navigate through all tabs (Home, Crops, Soil, Chatbot, Weed, Disease)
3. Test image upload functionality
4. Verify API responses in browser developer tools

---

## 🔒 **Security Configuration**

### **Production Security Checklist**
- [ ] Set strong `AGRISENSE_ADMIN_TOKEN`
- [ ] Configure proper `ALLOWED_ORIGINS`
- [ ] Use HTTPS in production
- [ ] Set up firewall rules
- [ ] Enable request rate limiting
- [ ] Configure proper CORS headers

### **SSL/TLS Setup**
For HTTPS, use a reverse proxy like Nginx:

```nginx
server {
    listen 443 ssl;
    server_name your-domain.com;
    
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    
    location / {
        proxy_pass http://localhost:8004;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

---

## 📊 **Performance Optimization**

### **Backend Optimization**
- Use `--workers 4` for multiple worker processes
- Configure database connection pooling
- Enable response caching for static endpoints
- Use async/await for I/O operations

### **Frontend Optimization**
- Frontend is pre-built and served statically
- Gzip compression enabled by default
- Assets are optimized and chunked
- Service worker disabled for stability

---

## 🐛 **Troubleshooting**

### **Common Issues**

**1. Server Won't Start**
```bash
# Check if port is in use
netstat -an | findstr :8004

# Kill existing process
taskkill /F /PID <process_id>
```

**2. Import Errors**
```bash
# Ensure you're in the correct directory
cd agrisense_app/backend

# Check Python path
python -c "import sys; print(sys.path)"
```

**3. Frontend Not Loading**
```bash
# Rebuild frontend
cd agrisense_app/frontend/farm-fortune-frontend-main
npm run build
```

**4. Database Issues**
```bash
# Reset SQLite database
rm sensors.db
# Server will recreate on next start
```

### **Log Files**
- **Server logs**: Console output from uvicorn
- **Application logs**: Check backend console for warnings/errors
- **Access logs**: Available in uvicorn output

---

## 📈 **Scaling Considerations**

### **Horizontal Scaling**
- Use load balancer (nginx, HAProxy)
- Deploy multiple backend instances
- Shared database configuration
- Session management for stateful operations

### **Database Scaling**
- Switch to PostgreSQL or MongoDB for production
- Configure read replicas
- Implement connection pooling
- Set up database backups

### **Monitoring**
- Set up application monitoring (Prometheus, Grafana)
- Configure alerting for health endpoints
- Monitor resource usage (CPU, memory, disk)
- Track API response times

---

## 🎯 **Success Metrics**

After deployment, verify:
- [ ] Server starts within 10 seconds
- [ ] All health endpoints return 200 OK
- [ ] Frontend loads completely
- [ ] API endpoints respond < 500ms
- [ ] No console errors in browser
- [ ] Image upload functionality works
- [ ] VLM analysis provides results

---

## 📞 **Support**

For deployment issues:
1. Check the troubleshooting section above
2. Review server logs for error messages
3. Verify all environment variables are set
4. Test with the provided test scripts
5. Check network connectivity and firewall settings

---

**Last Updated**: 2025-09-23 21:35 IST  
**Version**: 1.0.0  
**Deployment Status**: ✅ **PRODUCTION READY**
