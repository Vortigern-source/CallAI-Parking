# Use a lightweight Python image
FROM python:3.11-slim-bookworm

# Set the working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    git \
    nodejs \
    npm \
    supervisor \
    && rm -rf /var/lib/apt/lists/*

# Create necessary directories
RUN mkdir -p /var/log/supervisor \
    && mkdir -p /app/web-ui/backend/data

# Copy only package files first
COPY web-ui/package*.json ./web-ui/
WORKDIR /app/web-ui

# Install frontend dependencies
RUN npm ci

# Return to app directory and copy everything
WORKDIR /app
COPY . .

# Install Python dependencies
RUN pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt -U \
    && pip install --no-cache-dir -r web-ui/backend/requirements.txt -U

# Build frontend
WORKDIR /app/web-ui
RUN npm run build

# Return to app directory
WORKDIR /app

# Expose ports for all services
EXPOSE 8765 8000 3000

# Set environment variables
ENV PORT=8765
ENV FAST_API_PORT=8765
ENV DATABASE_URL="sqlite:///data/parking.db"

# Start supervisord
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]
