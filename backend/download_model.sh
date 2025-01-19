#!/bin/bash

MODEL_DIR="/app/storage/models/llm"
MODEL_PATH="$MODEL_DIR/mistral.gguf"
MODEL_URL="https://huggingface.co/TheBloke/Mistral-7B-Instruct-v0.2-GGUF/resolve/main/mistral-7b-instruct-v0.2.Q5_K_M.gguf"

# Create directories if they don't exist
mkdir -p "$MODEL_DIR"

# Check if model exists
if [ ! -f "$MODEL_PATH" ]; then
    echo "Downloading Llama 2 model..."
    wget -O "$MODEL_PATH" "$MODEL_URL"
else
    echo "Model already exists, skipping download"
fi

# Execute the passed command (usually the CMD from Dockerfile)
exec "$@" 