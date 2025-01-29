# Use official Ollama base image
FROM ollama/ollama:latest

# Set environment variables
ENV OLLAMA_HOST="0.0.0.0"
ENV OLLAMA_MODELS="/root/.ollama/models"

# Install curl for healthcheck
RUN apt-get update && \
    apt-get install -y curl && \
    rm -rf /var/lib/apt/lists/*

# Copy Modelfile for configuration
COPY Modelfile /tmp/Modelfile

# Expose Ollama API port
EXPOSE 11434

# Health check (corrected endpoint)
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl --fail http://localhost:11434 || exit 1

# Use the default entrypoint and command
ENTRYPOINT ["ollama"]
CMD ["serve"] 