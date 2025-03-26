FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libmagic1 \
    curl \
    procps \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt /app/requirements.txt

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade -r requirements.txt

# Copy application code
COPY . /app

# Create storage directories
# RUN mkdir -p /app/storage/models/embeddings

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV PORT=8001

# Expose port
EXPOSE 8001

# Command to run the application
# CMD ["uv", "run", "--with", "mcp", "mcp", "run", "mcp_server.py"]
CMD ["python", "mcp_server.py"]