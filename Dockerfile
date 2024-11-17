# Use a lightweight Python image
FROM python:3.11-slim-bookworm

# Set the working directory
WORKDIR /app

# Install system dependencies including git, nodejs, and npm
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    git \
    nodejs \
    npm \
    supervisor \
    && rm -rf /var/lib/apt/lists/*

# Create necessary directories for supervisord
RUN mkdir -p /var/log/supervisor

# Copy package.json first for frontend
COPY web-ui/package.json ./web-ui/

# Install frontend dependencies
WORKDIR /app/web-ui
RUN npm install

# Back to app root
WORKDIR /app

# Copy requirements files
COPY requirements.txt .
COPY web-ui/backend/requirements.txt web-ui/backend/

# Install Python dependencies
RUN pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt -U \
    && pip install --no-cache-dir -r web-ui/backend/requirements.txt -U

# Copy the custom llm_response.py file
COPY custom_pipecat/custom_processors/custom_aggregators/llm_response.py src/pipecat-ai/src/pipecat/processors/aggregators/llm_response.py

# Copy supervisord configuration
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Copy remaining application code
COPY . .

# Build frontend
WORKDIR /app/web-ui
RUN npm run build

# Back to app root
WORKDIR /app

# Create data directory for SQLite
RUN mkdir -p /app/web-ui/backend/data

# Expose ports for all services
EXPOSE 8765 8000 3000

# Set environment variables
ENV PORT=8765
ENV FAST_API_PORT=8765
ENV DATABASE_URL="sqlite:///data/parking.db"

# Start supervisord
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]
