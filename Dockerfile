# Use a lightweight Python image
FROM python:3.11-slim-bookworm

# Set the working directory
WORKDIR /app

# Install system dependencies including git
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy only the requirements file first (for better caching)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Copy only necessary application code
COPY . .

# Expose the port your server will run on
EXPOSE 8765

# Set environment variables (if needed)
ENV PORT=8765
ENV FAST_API_PORT=8765

# Start the server
CMD ["python", "server.py"]
