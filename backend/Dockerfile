FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && \
    apt-get install -y \
    build-essential \
    cmake \
    pkg-config \
    libopenblas-dev \
    wget \
    libmagic1 \
    dos2unix \
    && rm -rf /var/lib/apt/lists/*

# CPU-only build
ENV CMAKE_ARGS="-DLLAMA_CUBLAS=OFF"

# Install Python packages
COPY requirements.txt .
RUN pip install --no-cache-dir \
    llama-cpp-python==0.2.56 \
    --extra-index-url https://pypi.org/simple && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create models directory
RUN mkdir -p /app/storage/models/{llm,embeddings}

# Make download script executable
RUN dos2unix /app/download_model.sh && \
    chmod +x /app/download_model.sh

# Set Python path to include app directory
ENV PYTHONPATH=/app

# Use script as entrypoint
ENTRYPOINT ["/app/download_model.sh"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"] 