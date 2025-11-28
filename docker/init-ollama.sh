#!/bin/bash

# Script to initialize Ollama with required model
# This script pulls the model if it's not already available

MODEL_NAME="${OLLAMA_MODEL:-llama3.2:3b}"

echo "Checking if model $MODEL_NAME is available..."

# Wait for Ollama service to be ready
sleep 5

# Pull the model if not present
if ! ollama list | grep -q "$MODEL_NAME"; then
    echo "Pulling model $MODEL_NAME..."
    ollama pull "$MODEL_NAME"
    echo "Model $MODEL_NAME pulled successfully!"
else
    echo "Model $MODEL_NAME is already available."
fi

echo "Ollama initialization complete."
