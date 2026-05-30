# ---- Stage 1: build the React frontend ----
FROM node:20-alpine AS frontend
WORKDIR /app/frontend

# Install deps from the lockfile first (better layer caching)
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci

# Build the static site (outputs dist/, including public/hero.png)
COPY frontend/ ./
RUN npm run build

# ---- Stage 2: backend + built frontend ----
FROM python:3.12-slim
WORKDIR /app
ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# Python dependencies
COPY backend/requirements.txt ./
RUN pip install -r requirements.txt

# Backend source
COPY backend/ ./

# Built frontend -> ./static (FastAPI serves it on the same port as the API)
COPY --from=frontend /app/frontend/dist ./static

EXPOSE 9005
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "9005"]
