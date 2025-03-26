# User Guide: GraphRAG + AutoGen + Ollama

This guide covers how to use the integrated application that combines GraphRAG, AutoGen, and Ollama to provide a powerful knowledge retrieval system with conversational capabilities.

## Table of Contents

1. [Getting Started](#getting-started)
2. [Using the Interface](#using-the-interface)
3. [Search Methods](#search-methods)
4. [Adding Documents](#adding-documents)
5. [Working with AutoGen Agents](#working-with-autogen-agents)
6. [Troubleshooting](#troubleshooting)

## Getting Started

After installation and setup, you can start the application using the provided launcher:

- Windows: Double-click `launch.bat`

The application consists of two components:
- LiteLLM proxy server: Connects to Ollama for language model services
- Chainlit UI: Provides the web-based user interface

When the application starts, your browser should open automatically to the interface.

## Using the Interface

The interface includes:

- **Chat window**: Main area where you interact with the system
- **Settings panel**: Configure search method and LLM models
- **Status indicators**: Show the state of various system components
- **File uploader**: For adding new documents to the knowledge base

## Search Methods

The system offers two search methods:

### Graph-based Search (Global)

- Uses knowledge graph relationships between concepts
- Better for complex queries requiring understanding connections
- Example: "How does GraphRAG integrate with AutoGen's multi-agent framework?"

### Vector-based Search (Local)

- Uses direct similarity between the query and documents
- Better for straightforward factual queries
- Example: "What are the key features of GraphRAG?"

## Adding Documents

You can add new documents to the system:

1. Click the file upload button in the interface
2. Select Markdown (.md) files to upload
3. Choose to re-index immediately or later

If you choose to re-index later, you'll need to run:
```
python -m graphrag.index --root .
```

## Working with AutoGen Agents

Behind the scenes, the system uses AutoGen agents:

- **Assistant Agent**: Processes queries and generates responses
- **User Proxy Agent**: Handles function calling for document search

The agents automatically use the GraphRAG search function to find relevant information before answering questions.

## Troubleshooting

### LiteLLM Connection Issues

If you see "LiteLLM proxy server is not running":

1. Ensure Ollama is running
2. Try restarting the LiteLLM server:
   ```
   litellm --model ollama_chat/llama3 --port 8000
   ```
3. Check if the port is already in use

### No Documents Found

If searches return "No relevant documents found":

1. Make sure you've added documents to the `input/markdown` directory
2. Verify the GraphRAG index has been built
3. Try rebuilding the index:
   ```
   python -m graphrag.index --root .
   ```

### Model Loading Errors

If you encounter errors with Ollama models:

1. Check if the models are downloaded:
   ```
   ollama list
   ```
2. Pull any missing models:
   ```
   ollama pull llama3
   ollama pull mistral
   ollama pull nomic-embed-text
   ```

### UI Not Loading

If the Chainlit UI doesn't load:

1. Check if Chainlit is installed:
   ```
   pip show chainlit
   ```
2. Try reinstalling:
   ```
   pip install chainlit==2.1.1
   ```
3. Run manually:
   ```
   python -m chainlit run appUI_pro.py
   ```
