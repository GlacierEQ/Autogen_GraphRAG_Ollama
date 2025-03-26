"""
A simplified version of the GraphRAG + AutoGen + Ollama integration.
This version has fewer dependencies and is easier to run.
"""

import os
import sys
import autogen
import yaml
import traceback
import requests
from graphrag.query import searcher, search_query

print("Starting GraphRAG + AutoGen + Ollama integration...")

# Check for required directories
if not os.path.exists("output"):
    print("GraphRAG index not found.")
    print("Please run 'python init_graphrag.py' and 'python -m graphrag.index --root .' first.")
    sys.exit(1)

# Load GraphRAG settings
try:
    with open("settings.yaml", "r", encoding='utf-8') as file:
        settings = yaml.safe_load(file)
    print("✅ Settings loaded successfully")
except FileNotFoundError:
    print("❌ settings.yaml not found. Please run 'python init_graphrag.py' first.")
    sys.exit(1)

# Check if Ollama is running
try:
    response = requests.get("http://localhost:11434/api/version", timeout=3)
    if response.status_code == 200:
        print("✅ Ollama service is running")
    else:
        print("⚠️ Ollama service returned unexpected response")
except:
    print("❌ Ollama service is not running. Please start Ollama.")
    sys.exit(1)

# Check if LiteLLM proxy is running
try:
    response = requests.get("http://localhost:8000/health", timeout=3)
    if response.status_code == 200:
        print("✅ LiteLLM proxy is running")
    else:
        print("⚠️ LiteLLM proxy returned unexpected response")
except:
    print("❌ LiteLLM proxy is not running.")
    print("Please start it with: litellm --model ollama_chat/llama3 --port 8000")
    sys.exit(1)

# LLM Configuration for AutoGen
config_list_llama = [
    {
        "model": "llama3",
        "api_base": "http://localhost:8000/v1",
        "api_type": "open_ai",
        "api_key": "fake_key",
    }
]

# Set up the GraphRAG search function
def search_docs(query: str, is_global: bool = True) -> str:
    """Search documents using GraphRAG and return relevant information."""
    try:
        print(f"\nSearching documents with {'global' if is_global else 'local'} method: {query}")
        
        # Set up query parameters
        params = search_query.SearchQueryParameters(
            user_query=query,
            num_limit=10,
            similarity_top_k=6,
            make_global=is_global,
        )
        
        # Create searcher
        search = searcher.Searcher(root=os.path.abspath("."))
        
        # Perform search
        search_results = search.search_kg(params)
        
        # Extract results
        if search_results.local_results:
            doc_contents = []
            for doc in search_results.local_results:
                print(f"Found document: {doc.doc_id}")
                doc_contents.append(f"Document: {doc.doc_id}\nContent: {doc.content}")
            return "\n\n".join(doc_contents)
        else:
            print("No relevant documents found")
            return "No relevant documents found."
    except Exception as e:
        error_trace = traceback.format_exc()
        print(f"Error searching documents: {str(e)}\n{error_trace}")
        return f"Error searching documents: {str(e)}"

# Define function calling configuration
llm_config = {
    "config_list": config_list_llama,
    "timeout": 60,
    "functions": [
        {
            "name": "search_docs",
            "description": "Search documents to find relevant information for answering user questions",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query to find relevant documents"
                    },
                    "is_global": {
                        "type": "boolean",
                        "description": "Whether to perform a global (graph-based) search or just local similarity search"
                    }
                },
                "required": ["query"]
            }
        }
    ]
}

# Create AutoGen agents
user_proxy = autogen.UserProxyAgent(
    name="user_proxy",
    human_input_mode="TERMINATE",  # Allow user input until termination
    max_consecutive_auto_reply=0,
    code_execution_config={"work_dir": "coding"},
)

assistant = autogen.AssistantAgent(
    name="assistant",
    llm_config=llm_config,
    system_message="""You are a helpful AI assistant with access to a knowledge base. 
    When asked questions, use the search_docs function to find relevant information before providing answers.
    Always cite your sources and be clear about what you know and don't know.
    Use search_docs with is_global=True for complex questions that require understanding relationships, 
    and is_global=False for straightforward factual queries."""
)

# Register the search_docs function
user_proxy.register_function(
    function_map={"search_docs": search_docs}
)

# Start conversation
print("\n" + "="*50)
print("GraphRAG + AutoGen + Ollama Integration")
print("Type 'exit' to end the conversation")
print("="*50 + "\n")

user_proxy.initiate_chat(
    assistant, message="Hello! I'm ready to help answer your questions about the documents in the knowledge base."
)

# Continue the conversation until user exits
while True:
    user_input = input("\nYour question (or 'exit' to quit): ")
    if user_input.lower() == 'exit':
        print("\nGoodbye!")
        break
    
    # Reset the conversation for a new query
    user_proxy.send(user_input, assistant)
