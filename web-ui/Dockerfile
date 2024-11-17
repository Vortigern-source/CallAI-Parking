# Multi-stage build for frontend and backend

# Frontend Build Stage
FROM node:18-alpine AS frontend-build
WORKDIR /app/frontend

# Install dependencies
COPY web-ui/package*.json ./
RUN npm ci --only=production

# Copy frontend source
COPY web-ui/src ./src
COPY web-ui/public ./public
COPY web-ui/.env* ./

# Build frontend
RUN npm run build

# Backend Build Stage
FROM python:3.9-slim AS backend-build
WORKDIR /app/backend

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    nginx \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY web-ui/backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt \
    && pip install alembic uvicorn \
    # Explicitly install specific versions to resolve bcrypt warning
    && pip install --no-cache-dir \
        bcrypt==4.0.1 \
        passlib[bcrypt]==1.7.4

# Copy backend source
COPY web-ui/backend/ ./

# Final Stage
FROM python:3.9-slim
WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    nginx \
    && rm -rf /var/lib/apt/lists/*

# Create nginx user and group
RUN groupadd -r nginx && useradd -r -g nginx nginx

# Copy frontend build
COPY --from=frontend-build /app/frontend/build /app/frontend
COPY --from=backend-build /app/backend /app/backend
COPY --from=backend-build /usr/local/lib/python3.9/site-packages /usr/local/lib/python3.9/site-packages

# Nginx configuration
COPY web-ui/backend/nginx.conf /etc/nginx/nginx.conf

# Environment and startup script
COPY web-ui/backend/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Copy additional project files
COPY bot.py /app/bot.py
COPY custom_pipecat /app/custom_pipecat

# Create data directory with proper permissions
RUN mkdir -p /app/backend/data && chmod 777 /app/backend/data

# Expose port
EXPOSE 80

# Set environment
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV ALLOWED_ORIGINS=http://localhost:3000,https://mako-topical-arguably.ngrok-free.app
ENV INITIAL_ADMIN_USERNAME=admin
ENV INITIAL_ADMIN_EMAIL=admin@callgpt-parking.fly.dev
ENV INITIAL_ADMIN_PASSWORD=AdminInitialPassword123!
ENV DATABASE_URL=sqlite:////app/backend/data/parking.db

# Run as root to ensure all services can start
USER root

# Entrypoint
ENTRYPOINT ["/entrypoint.sh"]
