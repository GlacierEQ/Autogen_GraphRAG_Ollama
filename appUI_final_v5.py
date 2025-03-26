import os
import autogen
import chainlit as cl
import yaml
import sys
import traceback
import requests
from graphrag.query import searcher, search_query

# Check for required directories
if not os.path.exists("output"):
    cl.run_sync(cl.Message(
        content="GraphRAG index not found. Please run 'python init_graphrag.py' and 'python -m graphrag.index --root .' first.",
        author="system"
    ).send())
    print("GraphRAG index not found. Please run 'python init_graphrag.py' and 'python -m graphrag.index --root .' first.")
    sys.exit(1)

# Load GraphRAG settings
try:
    with open("settings.yaml", "r", encoding='utf-8') as file:
        graph_settings = yaml.safe_load(file)
except FileNotFoundError:
    cl.run_sync(cl.Message(
        content="settings.yaml not found. Please run 'python init_graphrag.py' first.",
        author="system"
    ).send())
    print("settings.yaml not found. Please run 'python init_graphrag.py' first.")
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

# Set up the GraphRAG search function for agent to use
def search_docs(query: str) -> str:
    """Search documents using GraphRAG and return relevant information."""
    try:
        # Set up query parameters
        params = search_query.SearchQueryParameters(
            user_query=query,
            num_limit=10,
            similarity_top_k=6,
            make_global=True,
        )
        
        # Create searcher
        search = searcher.Searcher(root=os.path.abspath("."))
        
        # Perform search
        search_results = search.search_kg(params)
        
        # Extract results
        if search_results.local_results:
            doc_contents = []
            for doc in search_results.local_results:
                doc_contents.append(f"Document: {doc.doc_id}\nContent: {doc.content}")
            return "\n\n".join(doc_contents)
        else:
            return "No relevant documents found."
    except requests.exceptions.RequestException as e:
        error_trace = traceback.format_exc()
        print(f"Error searching documents: {str(e)}\n{error_trace}")
        return f"Error searching documents: {str(e)}"

# Define AutoGen function calling configuration
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
    human_input_mode="NEVER",
    max_consecutive_auto_reply=0,
    code_execution_config={"work_dir": "coding"},
)

assistant = autogen.AssistantAgent(
    name="assistant",
    llm_config=llm_config,
    system_message="""You are a helpful AI assistant with access to a knowledge base. 
    When asked questions, use
