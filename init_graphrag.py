import os
import shutil
import subprocess
import sys

def create_directories():
    """Create necessary directories for GraphRAG"""
    os.makedirs("input", exist_ok=True)
    os.makedirs("input/markdown", exist_ok=True)
    os.makedirs("cache", exist_ok=True)
    os.makedirs("output", exist_ok=True)
    os.makedirs("coding", exist_ok=True)
    print("✅ Created directories")

def init_graphrag():
    """Initialize GraphRAG"""
    try:
        subprocess.run([sys.executable, "-m", "graphrag.index", "--init", "--root", "."], check=True)
        print("✅ Initialized GraphRAG")
    except subprocess.CalledProcessError:
        print("❌ Failed to initialize GraphRAG")
        return False
    return True

def copy_settings():
    """Copy settings.yaml to root directory"""
    try:
        shutil.copy("utils/settings.yaml", "settings.yaml")
        print("✅ Copied settings.yaml to root")
    except FileNotFoundError:
        print("❌ settings.yaml not found in utils directory")
        return False
    return True

def create_sample_docs():
    """Create sample markdown files for testing"""
    sample_docs = [
        {
            "name": "graphrag_intro.md",
            "content": """# Introduction to GraphRAG

GraphRAG is Microsoft's knowledge graph-enhanced RAG system that improves information retrieval by creating a knowledge graph from documents.

## Key Features

- **Global Search**: Uses graph relationships for complex queries
- **Local Search**: Uses vector similarity for direct factual queries
- **Entity Extraction**: Identifies key entities in documents
- **Relationship Building**: Creates connections between entities

GraphRAG integrates seamlessly with LLM applications to enhance context retrieval capabilities.
"""
        },
        {
            "name": "autogen_info.md",
            "content": """# AutoGen Framework

AutoGen is a framework for building LLM applications with multiple agents that can converse with each other to solve tasks.

## Key Components

- **AssistantAgent**: AI agent that can generate responses based on prompts
- **UserProxyAgent**: Acts on behalf of users to interact with other agents
- **Function Calling**: Allows agents to call functions to access external tools and data

AutoGen can be configured to use various LLMs including OpenAI models and local models via Ollama.
"""
        },
        {
            "name": "integration_guide.md",
            "content": """# Integrating GraphRAG with AutoGen

This guide explains how to combine GraphRAG's knowledge retrieval with AutoGen's multi-agent framework.

## Implementation Steps

1. Create a search function that uses GraphRAG's searcher
2. Register this function with an AutoGen UserProxyAgent
3. Configure the AssistantAgent to use this function for information retrieval
4. Set up proper prompt templates to guide the agent's use of search functions

This integration allows agents to have access to document knowledge through both vector similarity and graph-based search methods.
"""
        }
    ]
    
    for doc in sample_docs:
        filepath = os.path.join("input", "markdown", doc["name"])
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(doc["content"])
    
    print("✅ Created sample documents in input/markdown")

def main():
    print("Initializing GraphRAG environment...")
    create_directories()
    if not copy_settings():
        return
    if not init_graphrag():
        return
    create_sample_docs()
    print("\nEnvironment setup complete! Next steps:")
    print("1. Run 'python -m graphrag.index --root .' to index the documents")
    print("2. Start Lite-LLM proxy with 'litellm --model ollama_chat/llama3'")
    print("3. Run the application with 'chainlit run appUI.py'")

if __name__ == "__main__":
    main()
