# Installing Ollama on Windows

Ollama is a separate application that needs to be installed outside of Python.

## Step 1: Download Ollama

1. Visit the official Ollama website: [https://ollama.com/download/windows](https://ollama.com/download/windows)
2. Click the "Download" button to download the Windows installer

## Step 2: Install Ollama

1. Run the downloaded installer
2. Follow the on-screen instructions to complete the installation
3. After installation, Ollama will run in the system tray

## Step 3: Add Ollama to PATH

1. Right-click on "This PC" or "My Computer" and select "Properties"
2. Click on "Advanced system settings"
3. Click the "Environment Variables" button
4. In the "System variables" section, find the "Path" variable and click "Edit"
5. Click "New" and add: `C:\Program Files\Ollama`
6. Click "OK" to close all dialogs

## Step 4: Verify Installation

1. Open a new Command Prompt (you must open a new one after changing PATH)
2. Type `ollama --version` and press Enter
3. If installed correctly, you should see the Ollama version

## Step 5: Pull Required Models

After installation, open a Command Prompt and run:

```
ollama pull llama3
ollama pull mistral
ollama pull nomic-embed-text
```

This will download the required models for our application.
