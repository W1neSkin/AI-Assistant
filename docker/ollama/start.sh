#!/bin/bash

# Start Ollama service in the background
ollama serve &

# Wait for Ollama to start
sleep 5

# Create model with custom parameters if not present
if ! ollama list | grep -q "deepseek-r1:7b"; then
    echo "Pulling and configuring deepseek-r1:7b model..."
    ollama pull deepseek-r1:7b
    
    # Create custom model with optimized parameters
    cat > /tmp/Modelfile << EOF
FROM deepseek-r1:7b

# GPU Configuration
PARAMETER num_gpu_layers 35
PARAMETER gpu_memory_utilization 0.8

# Model Parameters
PARAMETER num_ctx 4096
PARAMETER num_thread 4
PARAMETER num_batch 512
PARAMETER temperature 0.7
PARAMETER top_p 0.9
PARAMETER repeat_penalty 1.1

# Memory Configuration
PARAMETER rope_frequency_base 10000
PARAMETER rope_frequency_scale 1.0
EOF
    
    ollama create optimized-deepseek-r1:7b -f /tmp/Modelfile
fi

# Keep container running and handle signals properly
trap "exit" TERM
while true; do
    sleep 1
done 