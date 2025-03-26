import os
import sys
import autogen
import chainlit as cl
from chainlit.types import AskFileResponse
import yaml
import traceback
import requests
from datetime import datetime
from graphrag.query import searcher, search_query
from typing import List, Dict, Any, Optional
from flask import Flask, request, jsonify
from threading import Thread

app = Flask(__name__)

CONFIG_FILE = "app_config.yaml"

@app.route('/save_config', methods=['POST'])
def save_config():
    config_data = request.get_json()
    print("Received configuration:", config_data)
    
    try:
        with open(CONFIG_FILE, 'w') as file:
            yaml.dump(config_data, file)
        return jsonify({'status': 'success', 'message': 'Configuration saved successfully!'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

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

# System status variables
system_status = {
    "graphrag_ready": True,
    "litellm_ready": False,
    "ollama_ready": False,
    "last_checked": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
}

# Document statistics (will be populated in on_chat_start)
doc_stats = {
    "total_docs": 0,
    "total_entities": 0,
    "total_relations": 0,
    "doc_types": {}
}

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
def search_docs(query: str, is_global: bool = True) -> str:
    """Search documents using GraphRAG and return relevant information."""
    try:
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
                doc_contents.append(f"Document: {doc.doc_id}\nContent: {doc.content}")
            return "\n\n".join(doc_contents)
        else:
            return "No relevant documents found."
    except Exception as e:
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
    and is_global=False for straightforward factual queries.
    Format your responses in Markdown for better readability."""
)

def check_services() -> Dict[str, bool]:
    """Check if required services are running."""
    status = {"litellm": False, "ollama": False}
    
    # Check LiteLLM proxy
    try:
        response = requests.get("http://localhost:8000/health", timeout=3)
        status["litellm"] = response.status_code == 200
    except:
        pass
    
    # Check Ollama
    try:
        response = requests.get("http://localhost:11434/api/version", timeout=3)
        status["ollama"] = response.status_code == 200
    except:
        pass
    
    return status

def get_document_stats() -> Dict[str, Any]:
    """Get statistics about indexed documents."""
    stats = {
        "total_docs": 0,
        "total_entities": 0,
        "total_relations": 0,
        "doc_types": {}
    }
    
    # Count files in input directory
    input_dir = os.path.join(os.path.abspath("."), "input")
    if os.path.exists(input_dir):
        for root, _, files in os.walk(input_dir):
            for file in files:
                ext = os.path.splitext(file)[1].lower()
                if ext not in stats["doc_types"]:
                    stats["doc_types"][ext] = 0
                stats["doc_types"][ext] += 1
                stats["total_docs"] += 1
    
    # Could add more sophisticated stats from GraphRAG if available
    return stats

# Custom components
def status_indicator(name: str, status: bool) -> cl.Component:
    """Create a status indicator component."""
    color = "green" if status else "red"
    return cl.Text(
        name=f"status_{name}",
        content=f"● {name.capitalize()}: {'Online' if status else 'Offline'}",
        display="inline",
        classes=[f"status-{color}"]
    )

# Add a markdown file for display
async def add_document_markdown(doc_id: str, content: str) -> None:
    """Format and display document content as markdown."""
    element = cl.Markdown(
        content=f"""
### Document: {doc_id}
```
{content[:300]}{"..." if len(content) > 300 else ""}
```
""",
        classes=["document-reference"]
    )
    await element.send()

# Chainlit UI setup
@cl.on_chat_start
async def on_chat_start():
    # Set default settings
    cl.user_session.set("search_method", "global")
    cl.user_session.set("model", "llama3")
    
    # Check services
    services = check_services()
    system_status["litellm_ready"] = services["litellm"]
    system_status["ollama_ready"] = services["ollama"]
    
    # Get document stats
    global doc_stats
    doc_stats = get_document_stats()
    
    # Display welcome message with system status
    if not services["litellm"]:
        await cl.Message(
            content="⚠️ LiteLLM proxy server is not running. Please start it with:\n```\nlitellm --model ollama_chat/llama3 --port 8000\n```",
            author="system"
        ).send()
    
    if not services["ollama"]:
        await cl.Message(
            content="⚠️ Ollama service is not detected. Please ensure it's installed and running.",
            author="system"
        ).send()
    
    # Create status indicators
    await cl.Message(content="# GraphRAG + AutoGen + Ollama").send()
    
    status_text = (
        f"**System Status**\n\n"
        f"- LiteLLM Proxy: {'✅ Online' if services['litellm'] else '❌ Offline'}\n"
        f"- Ollama Service: {'✅ Online' if services['ollama'] else '❌ Offline'}\n"
        f"- GraphRAG Index: {'✅ Ready' if system_status['graphrag_ready'] else '❌ Not Ready'}\n\n"
        f"**Document Stats**\n\n"
        f"- Total Documents: {doc_stats['total_docs']}\n"
        f"- Document Types: {', '.join([f'{ext} ({count})' for ext, count in doc_stats['doc_types'].items()])}\n"
    )
    
    await cl.Message(content=status_text).send()
    
    # Create UI settings
    await cl.ChatSettings(
        [
            cl.Select(
                id="search_method",
                label="Search Method",
                values=[
                    cl.Option(value="global", label="Graph-based (connections between concepts)"),
                    cl.Option(value="local", label="Vector-based (direct similarity)")
                ],
                initial_value="global",
            ),
            cl.Select(
                id="model",
                label="Ollama Model",
                values=[
                    cl.Option(value="llama3", label="Llama 3 (balanced)"),
                    cl.Option(value="mistral", label="Mistral (faster)")
                ],
                initial_value="llama3",
            ),
        ]
    ).send()
    
    # Create sidebar with information
    await cl.Text(content="## GraphRAG + AutoGen + Ollama", name="sidebar-title").send()
    await cl.Text(content="Knowledge Graph-Enhanced RAG with LLM Agents", name="sidebar-subtitle").send()
    
    # Add file upload capability
    await cl.Message(
        content="Welcome to GraphRAG + AutoGen + Ollama integration! I can help you search through documents. How can I assist you?\n\nYou can also upload new documents using the file upload button below.",
        author="assistant"
    ).send()

@cl.on_settings_update
async def on_settings_update(settings):
    cl.user_session.set("search_method", settings["search_method"])
    cl.user_session.set("model", settings["model"])
    
    # Update LLM config if model changed
    if settings["model"] != cl.user_session.get("prev_model", "llama3"):
        cl.user_session.set("prev_model", settings["model"])
        config_list_llama[0]["model"] = settings["model"]
        
        # Create new assistant with updated config
        new_llm_config = {**llm_config, "config_list": config_list_llama}
        cl.user_session.set("llm_config", new_llm_config)
    
    await cl.Message(
        content=f"Settings updated:\n- Search Method = {settings['search_method']}\n- Model = {settings['model']}",
        author="assistant"
    ).send()

@cl.on_message
async def on_message(message: cl.Message):
    query = message.content
    search_method = cl.user_session.get("search_method", "global")
    is_global = search_method == "global"
    
    # Create a new message for showing results
    msg = cl.Message(author="assistant", content="")
    await msg.send()
    
    # Show typing indicator
    await msg.update(content="Searching documents and generating response...")
    
    # Register search function with user_proxy
    user_proxy.register_function(
        function_map={"search_docs": lambda query, is_global=True: search_docs(query, is_global)}
    )
    
    # Start conversation with AutoGen agents
    user_proxy.initiate_chat(
        assistant, message=query
    )
    
    # Get the last message from the assistant
    last_message = assistant.last_message()
    
    # Update the UI with the final response
    await msg.update(content=last_message["content"])

@cl.on_file_upload
async def on_file_upload(files: List[cl.File]) -> None:
    """Handle file uploads."""
    # Create message to show progress
    msg = cl.Message(author="system", content="Processing uploaded files...")
    await msg.send()
    
    input_dir = os.path.join("input", "markdown")
    os.makedirs(input_dir, exist_ok=True)
    
    file_list = []
    for file in files:
        # Save file to input directory
        file_path = os.path.join(input_dir, file.name)
        with open(file_path, "wb") as f:
            f.write(file.content)
        file_list.append(file.name)
    
    # Update message with status
    await msg.update(content=f"Files uploaded successfully: {', '.join(file_list)}\n\nTo index these files, please run:\n```\npython -m graphrag.index --root .\n```")
    
    # Offer to re-index
    await cl.AskActionMessage(
        content="Would you like to re-index the documents now?",
        actions=[
            cl.Action(name="reindex", value="yes", label="Yes, re-index now"),
            cl.Action(name="later", value="no", label="No, I'll do it later")
        ]
    ).send()

@cl.on_action
async def on_action(action: cl.Action):
    """Handle user actions."""
    if action.name == "reindex" and action.value == "yes":
        # Show progress message
        msg = cl.Message(author="system", content="Re-indexing documents... This may take a few minutes.")
        await msg.send()
        
        try:
            # Run GraphRAG indexing
            import subprocess
            result = subprocess.run(
                [sys.executable, "-m", "graphrag.index", "--root", "."],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                await msg.update(content="✅ Documents have been re-indexed successfully!")
            else:
                await msg.update(content=f"❌ Error re-indexing documents:\n```\n{result.stderr}\n```")
        except Exception as e:
            await msg.update(content=f"❌ Error re-indexing documents: {str(e)}")

def run_flask():
    app.run(host='localhost', port=5000)  # Choose an appropriate port

if __name__ == "__main__":
    flask_thread = Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()
    cl.run()
````
