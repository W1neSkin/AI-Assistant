#!/bin/bash

MODEL_NAME="deepseek-r1:7b"
OLLAMA_HOST="http://localhost:11434"

# Check current model version
CURRENT_VERSION=$(curl -s $OLLAMA_HOST/tags | jq -r ".models[] | select(.name == \"$MODEL_NAME\") | .digest")

# Pull latest version
curl -X POST $OLLAMA_HOST/api/pull -d "{
  \"name\": \"$MODEL_NAME\"
}"

# Remove old version if updated
NEW_VERSION=$(curl -s $OLLAMA_HOST/tags | jq -r ".models[] | select(.name == \"$MODEL_NAME\") | .digest")
if [ "$CURRENT_VERSION" != "$NEW_VERSION" ] && [ -n "$CURRENT_VERSION" ]; then
  curl -X DELETE $OLLAMA_HOST/api/delete -d "{
    \"name\": \"$MODEL_NAME:$CURRENT_VERSION\"
  }"
fi 