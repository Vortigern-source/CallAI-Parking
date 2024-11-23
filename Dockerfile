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
    nginx \
    && rm -rf /var/lib/apt/lists/* && \
    mkdir -p /run/nginx

# Create necessary directories for supervisord
RUN mkdir -p /var/log/supervisor

# Copy requirements files first
COPY requirements.txt .
COPY web-ui/backend/requirements.txt web-ui/backend/
COPY web-ui/backend/nginx.conf /etc/nginx/conf.d/default.conf

# Create required nginx directories
RUN mkdir -p /var/log/nginx && \
    mkdir -p /var/lib/nginx && \
    touch /var/log/nginx/error.log && \
    touch /var/log/nginx/access.log

# Ensure correct permissions
RUN chown -R www-data:www-data /var/lib/nginx && \
    chown -R www-data:www-data /var/log/nginx

# Install Python dependencies
RUN pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt -U \
    && pip install --no-cache-dir -r web-ui/backend/requirements.txt -U

# Copy the custom llm_response.py file
COPY custom_pipecat/custom_processors/custom_aggregators/llm_response.py src/pipecat-ai/src/pipecat/processors/aggregators/llm_response.py

# Copy supervisord configuration
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Copy application code
COPY . .

# Build frontend for production
WORKDIR /app/web-ui
RUN npm install
RUN npm run build
RUN echo "Frontend build files:" && ls -la build/

# Create backend static directory and copy frontend build files
RUN mkdir -p /app/web-ui/backend/static && \
    cp -r build/* /app/web-ui/backend/static/ && \
    echo "Static directory contents:" && \
    ls -R /app/web-ui/backend/static/

# Back to app root
WORKDIR /app

# Create data directory for SQLite
RUN mkdir -p /app/web-ui/backend/data

# Expose ports for backend services
EXPOSE 8765 8000

# Set environment variables
ENV PORT=8765
ENV FAST_API_PORT=8765
ENV DATABASE_URL="sqlite:///data/parking.db"
ENV NODE_ENV=production

# Add verification step
RUN echo "Verifying static files:" && \
    ls -R /app/web-ui/backend/static/ && \
    echo "Checking specific files:" && \
    for file in \
        "/app/web-ui/backend/static/index.html" \
        "/app/web-ui/backend/static/asset-manifest.json" \
        "/app/web-ui/backend/static/static/js/main.bd332e19.js"; \
    do \
        if [ -f "$file" ]; then \
            echo "✓ $file exists"; \
        else \
            echo "✗ $file missing" && exit 1; \
        fi \
    done

# Start supervisord
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]
