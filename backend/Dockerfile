FROM python:3.11-slim
WORKDIR /app

# Install system dependencies first
RUN apt-get update && \
    apt-get install -y \
    build-essential \
    cmake \
    pkg-config \
    libopenblas-dev \
    wget \
    libmagic1 \
    && rm -rf /var/lib/apt/lists/*

# Then copy and install Python requirements
COPY requirements.txt .
COPY requirements-test.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir -r requirements-test.txt

COPY . .

# Development stage
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONDEVMODE=1 \
    DEBUG_MODE=true

# Set Python path to include app directory
ENV PYTHONPATH=/app

# Start the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"] 