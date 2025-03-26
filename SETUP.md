# Complete Setup Guide for GraphRAG + AutoGen + Ollama

This guide provides step-by-step instructions to set up the complete environment for GraphRAG + AutoGen + Ollama integration.

## Prerequisites

- Windows 10 or 11
- Python 3.10+ installed
- Admin access to install software

## Step 1: Install Ollama

Ollama is required to run local LLMs:

1. Follow the instructions in `install_ollama.md`
2. Verify Ollama is running by opening a new Command Prompt and typing:
   ```
   ollama list
   ```

## Step 2: Set Up Python Environment

1. Open Command Prompt in the project directory
2. Run the setup script:
   ```
   setup_env.bat
   ```
3. Activate the virtual environment:
   ```
   venv\Scripts\activate
   ```

## Step 3: Verify Dependencies

1. With your virtual environment activated, run:
   ```
   python utils\check_deps.py
   ```
2. All dependencies should show as installed (✅)

## Step 4: Install Required Ollama Models

If you haven't already pulled the models:

```
ollama pull llama3
ollama pull mistral
ollama pull nomic-embed-text
```

## Step 5: Initialize GraphRAG

1. Run the initialization script:
   ```
   python init_graphrag.py
   ```
2. Build the knowledge graph:
   ```
   python -m graphrag.index --root .
   ```

## Step 6: Start the Application

1. Start LiteLLM proxy in a new Command Prompt window with venv activated:
   ```
   litellm --model ollama_chat/llama3 --port 8000
   ```
2. In another Command Prompt window with venv activated, start the Chainlit app:
   ```
   chainlit run appUI.py
   ```
3. Open your browser and go to: http://localhost:8000 to access the application

## Troubleshooting

### Module Not Found Errors
- Make sure the virtual environment is activated
- Try reinstalling the package: `pip install <package-name>`

### Chainlit Not Recognized
- Ensure you're running the command within the activated virtual environment
- Try reinstalling: `pip install chainlit`

### GraphRAG Initialization Fails
- Check if graphrag is installed: `pip show graphrag`
- Try reinstalling: `pip install graphrag`

### Ollama Not Found
- Make sure Ollama is installed and added to PATH
- Try restarting your Command Prompt after installation
- Verify Ollama is running in the system tray
