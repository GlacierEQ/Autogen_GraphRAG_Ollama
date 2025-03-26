#!/bin/bash

echo "Starting GraphRAG + AutoGen + Ollama + Chainlit application..."

# Check if documents are indexed
if [ ! -d "output" ]; then
    echo "Initializing GraphRAG environment..."
    python init_graphrag.py
    
    echo "Indexing documents..."
    python -m graphrag.index --root .
fi

# Check if Ollama models are available
echo "Checking Ollama models..."
ollama list

# Start LiteLLM proxy server
echo "Starting LiteLLM proxy server on port 8000..."
litellm --model ollama_chat/llama3 --port 8000 &
LITELLM_PID=$!

# Wait for LiteLLM server to start
echo "Waiting for LiteLLM server to start..."
sleep 5

# Start Chainlit app
echo "Starting Chainlit application..."
chainlit run appUI.py

# Clean up
kill $LITELLM_PID
echo "Application stopped."
