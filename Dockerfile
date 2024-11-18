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

# Copy the entire web-ui directory
COPY web-ui /app/web-ui

# Install and build frontend
WORKDIR /app/web-ui
RUN npm install && \
    npm run build

# Copy the rest of the application
WORKDIR /app
COPY . .

# Install Python dependencies
RUN pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt -U \
    && pip install --no-cache-dir -r web-ui/backend/requirements.txt -U

# Ensure supervisord config is in the correct location
RUN cp /app/supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Expose ports for all services
EXPOSE 8765 8000 3000

# Set environment variables
ENV PORT=8765
ENV FAST_API_PORT=8765
ENV DATABASE_URL="sqlite:///data/parking.db"
ENV NODE_ENV=production

# Start supervisord
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]
