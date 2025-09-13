# Multi-stage build: frontend (Vite) + backend (FastAPI)

# 1) Build frontend
FROM node:18-alpine AS frontend
WORKDIR /app
# Copy only frontend package files to leverage caching
COPY agrisense_app/frontend/farm-fortune-frontend-main/package*.json ./
RUN npm ci || npm install
COPY agrisense_app/frontend/farm-fortune-frontend-main/ ./
RUN npm run build

# 2) Backend image
FROM python:3.9-slim
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    AGRISENSE_DISABLE_ML=1 \
    PORT=8004
WORKDIR /app

# System deps that help with numpy/pandas wheels
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy backend requirements (dev excludes TensorFlow to keep image light)
COPY agrisense_app/backend/requirements-dev.txt ./requirements.txt
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy backend source
COPY agrisense_app/ ./agrisense_app/

# Copy built frontend into the location the backend serves from
# main.py prefers nested dist: backend/../frontend/farm-fortune-frontend-main/dist
RUN mkdir -p agrisense_app/frontend/farm-fortune-frontend-main/dist
COPY --from=frontend /app/dist/ ./agrisense_app/frontend/farm-fortune-frontend-main/dist/

EXPOSE 8004
CMD ["python", "-m", "uvicorn", "agrisense_app.backend.main:app", "--host", "0.0.0.0", "--port", "8004"]
