@echo off
echo Starting GraphRAG + AutoGen + Ollama + Chainlit application...

REM Check if documents are indexed
if not exist "output" (
    echo Initializing GraphRAG environment...
    python init_graphrag.py
    
    echo Indexing documents...
    python -m graphrag.index --root .
)

REM Check if Ollama models are available
echo Checking Ollama models...
ollama list

REM Start LiteLLM proxy server
echo Starting LiteLLM proxy server on port 8000...
start cmd /k "title LiteLLM Proxy && litellm --model ollama_chat/llama3 --port 8000"

REM Wait for LiteLLM server to start
timeout /t 5 /nobreak

REM Start Chainlit app
echo Starting Chainlit application...
chainlit run appUI.py

echo Application stopped.
