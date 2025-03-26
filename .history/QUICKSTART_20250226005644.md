# Quick Start Guide: GraphRAG + AutoGen + Ollama

This guide will help you get up and running with the GraphRAG + AutoGen + Ollama integration quickly.

## Prerequisites

- Python 3.10+ installed
- Ollama installed (https://ollama.com)
- Required Ollama models:
  - llama3
  - mistral
  - nomic-embed-text

## Step 1: Setup Environment

### Windows:

```powershell
# Create virtual environment
python -m venv venv
.\venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Check dependencies
python utils/check_deps.py
```

### Linux/Mac:

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Check dependencies
python utils/check_deps.py
```

## Step 2: Initialize GraphRAG

```bash
# Run the initialization script
python init_graphrag.py

# Index the documents
python -m graphrag.index --root .
```

## Step 3: Start Services

### Manual Start:

1. Start Ollama service (if not running):
   ```bash
   ollama serve
   ```

2. Start LiteLLM proxy server:
   ```bash
   litellm --model ollama_chat/llama3 --port 8000
   ```

3. Start the Chainlit application:
   ```bash
   chainlit run appUI.py
   ```

### Automatic Start:
- Windows: Run `start.bat`
- Linux/Mac: Run `bash start.sh`

## Step 4: Access the Application

Open your browser and go to http://localhost:8000 to access the Chainlit UI.

## Step 5: Add Your Own Documents

Place your documents in the `input/markdown` directory and re-index:

```bash
python -m graphrag.index --root .
```

## Troubleshooting

1. **Ollama models not found:**
   ```bash
   ollama pull llama3
   ollama pull mistral
   ollama pull nomic-embed-text
   ```

2. **GraphRAG initialization fails:**
   - Check that the GraphRAG package is installed correctly
   - Verify that the modified embedding files are in place

3. **LiteLLM proxy server fails:**
   - Check if port 8000 is already in use
   - Try using a different port with `--port 8001` and update appUI.py accordingly

4. **Chainlit UI doesn't connect to LLM:**
   - Verify the LiteLLM proxy is running
   - Check the URL and port in appUI.py match your LiteLLM proxy settings

## Advanced: Custom Configuration

To customize the GraphRAG settings, edit the `settings.yaml` file. Important settings include:
- Embedding model configuration
- Linking threshold for graph relationships
- Document source directory
