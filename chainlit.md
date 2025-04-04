# GraphRAG + AutoGen + Ollama + Chainlit

## What is this app?

This application integrates several powerful technologies to create a fully local and free multi-agent RAG (Retrieval-Augmented Generation) system:

- **GraphRAG**: Microsoft's knowledge graph-enhanced RAG system
- **AutoGen**: Microsoft's multi-agent framework
- **Ollama**: Local LLM serving platform
- **Chainlit**: Interactive UI for conversational AI

## How to use

1. Ask any question related to the documents in your knowledge base
2. Use the settings panel to configure:
   - Search method (global or local)
   - Ollama model to use

## Examples

Try asking questions like:
- "What are the key features of GraphRAG?"
- "How does AutoGen work with local LLMs?"
- "Summarize the technical architecture of this application"

## Under the hood

This application uses:
- Local embedding models (Nomic-embed-text) for vector representations
- Local LLMs (Llama3/Mistral) for inference
- Graph-based search for complex queries
- Multi-agent interactions through AutoGen
