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
    When asked questions, use the search_docs function to find relevant information before providing answers.
    Always cite your sources and be clear about what you know and don't know.
    Use search_docs with is_global=True for complex questions that require understanding relationships, 
    and is_global=False for straightforward factual queries."""
)

# Chainlit UI setup
@cl.on_chat_start
async def on_chat_start():
    cl.user_session.set("search_method", "global")
    
    # Check if LiteLLM proxy is running
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code != 200:
            await cl.Message(
                content="⚠️ LiteLLM proxy server might not be running. Some features may not work.",
                author="system"
            ).send()
    except requests.exceptions.RequestException:
        await cl.Message(
            content="⚠️ LiteLLM proxy server is not running. Please start it with 'litellm --model ollama_chat/llama3 --port 8000'",
            author="system"
        ).send()
    
    # Create UI settings
    await cl.ChatSettings(
        [
            cl.Select(
                id="search_method",
                label="Search Method",
                values=["global", "local"],
                initial_value="global",
            ),
            cl.Select(
                id="model",
                label="Ollama Model",
                values=["llama3", "mistral"],
                initial_value="llama3",
            ),
        ]
    ).send()
    
    await cl.Message(
        content="Welcome to GraphRAG + AutoGen + Ollama integration! I can help you search through documents. How can I assist you?",
        author="assistant"
    ).send()

@cl.on_settings_update
async def on_settings_update(settings):
    cl.user_session.set("search_method", settings["search_method"])
    cl.user_session.set("model", settings["model"])
    
    await cl.Message(
        content=f"Settings updated: Search Method = {settings['search_method']}, Model = {settings['model']}",
        author="assistant"
    ).send()

@cl.on_message
async def on_message(message: cl.Message):
    query = message.content
    search_method = cl.user_session.get("search_method", "global")
    
    # Create a new message for showing results
    msg = cl.Message(author="assistant", content="")
    await msg.send()
    
    # Update message with thinking indicator
    await msg.update(content="Searching documents and generating response...")
    
    # Start conversation with AutoGen agents
    user_proxy.initiate_chat(
        assistant, message=query
    )
    
    # Get the last message from the assistant
    last_message = assistant.last_message()
    
    # Update the UI with the final response
    await msg.update(content=last_message["content"])

if __name__ == "__main__":
    # This will be run by Chainlit
    pass
