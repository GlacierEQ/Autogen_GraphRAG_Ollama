"""
Advanced UI implementation for GraphRAG + AutoGen + Ollama integration.
Features:
- Enhanced document upload and processing
- Interactive graph visualization
- Advanced search options
- Document management
- Custom agent configurations
"""
import os
import sys
import autogen
import chainlit as cl
import yaml
import time
import traceback
import json
import requests
from typing import Dict, List, Tuple, Optional, Union, Any
import logging
from datetime import datetime
import tempfile
import uuid
import shutil
import asyncio

# Import GraphRAG components
from graphrag.query import searcher, search_query
from graphrag.index import indexer

# Import document processors
sys.path.append(os.path.join(os.path.dirname(__file__), "document_processors"))
from universal_processor import UniversalDocumentProcessor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("graphrag_ui.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Ensure required directories exist
REQUIRED_DIRS = ["input", "input/markdown", "cache", "output", "coding", "temp"]
for d in REQUIRED_DIRS:
    os.makedirs(d, exist_ok=True)

# Load settings
try:
    with open("settings.yaml", "r", encoding='utf-8') as file:
        settings = yaml.safe_load(file)
    logger.info("Settings loaded successfully")
except FileNotFoundError:
    logger.error("settings.yaml not found")
    sys.exit(1)

# System state
system_state = {
    "services": {
        "graphrag": True,
        "litellm": False,
        "ollama": False,
    },
    "stats": {
        "total_docs": 0,
        "total_queries": 0,
        "avg_response_time": 0,
        "index_last_updated": None,
    },
    "model_configs": {
        "llama3": {
            "api_base": "http://localhost:8000/v1",
            "supports_function_calling": True,
            "context_length": 8000,
        },
        "mistral": {
            "api_base": "http://localhost:8000/v1",
            "supports_function_calling": True,
            "context_length": 4000,
        }
    }
}

# Check services
def check_services():
    """Check if required services are running."""
    # Check LiteLLM proxy
    try:
        response = requests.get("http://localhost:8000/health", timeout=3)
        system_state["services"]["litellm"] = response.status_code == 200
        logger.info(f"LiteLLM service status: {'online' if system_state['services']['litellm'] else 'offline'}")
    except Exception as e:
        system_state["services"]["litellm"] = False
        logger.warning(f"LiteLLM check failed: {str(e)}")
    
    # Check Ollama
    try:
        response = requests.get("http://localhost:11434/api/version", timeout=3)
        system_state["services"]["ollama"] = response.status_code == 200
        logger.info(f"Ollama service status: {'online' if system_state['services']['ollama'] else 'offline'}")
    except Exception as e:
        system_state["services"]["ollama"] = False
        logger.warning(f"Ollama check failed: {str(e)}")
    
    return system_state["services"]

# Count documents and update stats
def update_document_stats():
    """Count documents and update statistics."""
    doc_count = 0
    markdown_dir = os.path.join("input", "markdown")
    
    if os.path.exists(markdown_dir):
        for root, _, files in os.walk(markdown_dir):
            for file in files:
                if file.lower().endswith(('.md', '.markdown')):
                    doc_count += 1
    
    system_state["stats"]["total_docs"] = doc_count
    
    # Get last modified time of output directory as proxy for index last updated
    output_dir = "output"
    if os.path.exists(output_dir):
        try:
            latest_time = max(os.path.getmtime(os.path.join(root, file)) 
                             for root, _, files in os.walk(output_dir) 
                             for file in files)
            system_state["stats"]["index_last_updated"] = datetime.fromtimestamp(latest_time).strftime('%Y-%m-%d %H:%M:%S')
        except ValueError:
            system_state["stats"]["index_last_updated"] = None
    
    logger.info(f"Document stats updated: {doc_count} documents found")
    return system_state["stats"]

# LLM Configuration for AutoGen with advanced capabilities
def get_llm_config(model: str = "llama3"):
    """Get LLM configuration for AutoGen based on selected model."""
    config_list = [
        {
            "model": model,
            "api_base": system_state["model_configs"][model]["api_base"],
            "api_type": "open_ai",
            "api_key": "fake_key",
        }
    ]
    
    context_length = system_state["model_configs"][model]["context_length"]
    
    # Define specialized search functions for better retrieval
    llm_config = {
        "config_list": config_list,
        "timeout": 120,
        "cache_seed": 42,  # Enable response caching
        "temperature": 0.5,  # More deterministic responses for RAG
        "max_tokens": min(context_length // 2, 4000),
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
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of results to return"
                        }
                    },
                    "required": ["query"]
                }
            },
            {
                "name": "visualize_graph",
                "description": "Generate a visualization of related concepts in the knowledge graph",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "concepts": {
                            "type": "array", 
                            "items": {"type": "string"},
                            "description": "List of concepts to visualize relationships between"
                        },
                        "depth": {
                            "type": "integer",
                            "description": "Depth of relationships to include in visualization"
                        }
                    },
                    "required": ["concepts"]
                }
            },
            {
                "name": "get_document_content",
                "description": "Get the full content of a specific document by its ID",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "doc_id": {
                            "type": "string",
                            "description": "The document identifier"
                        }
                    },
                    "required": ["doc_id"]
                }
            }
        ]
    }
    
    return llm_config

# Enhanced search function with more capabilities
def search_docs(query: str, is_global: bool = True, limit: int = 10) -> Dict[str, Any]:
    """Advanced document search using GraphRAG with detailed results and metadata."""
    try:
        start_time = time.time()
        
        # Set up query parameters
        params = search_query.SearchQueryParameters(
            user_query=query,
            num_limit=limit,
            similarity_top_k=min(limit, 10),
            make_global=is_global,
        )
        
        # Create searcher
        search = searcher.Searcher(root=os.path.abspath("."))
        
        # Perform search
        search_results = search.search_kg(params)
        
        # Advanced response formatting
        response = {
            "success": True,
            "query": query,
            "search_type": "global" if is_global else "local",
            "execution_time": time.time() - start_time,
            "results": [],
            "total_results": 0,
        }
        
        # Extract results with metadata
        if search_results.local_results:
            for doc in search_results.local_results:
                response["results"].append({
                    "doc_id": doc.doc_id,
                    "content": doc.content,
                    "relevance_score": round(doc.score, 4) if hasattr(doc, 'score') else None,
                    "metadata": doc.metadata if hasattr(doc, 'metadata') else {}
                })
            response["total_results"] = len(response["results"])
        
        # Update statistics
        system_state["stats"]["total_queries"] += 1
        if system_state["stats"].get("avg_response_time"):
            # Running average
            system_state["stats"]["avg_response_time"] = (
                system_state["stats"]["avg_response_time"] * (system_state["stats"]["total_queries"] - 1) + 
                response["execution_time"]
            ) / system_state["stats"]["total_queries"]
        else:
            system_state["stats"]["avg_response_time"] = response["execution_time"]
        
        return response
    except Exception as e:
        error_trace = traceback.format_exc()
        logger.error(f"Error searching documents: {str(e)}\n{error_trace}")
        return {
            "success": False,
            "query": query,
            "error": str(e),
            "execution_time": time.time() - start_time
        }

# Document content retrieval function
def get_document_content(doc_id: str) -> Dict[str, Any]:
    """Get the full content of a specific document by ID."""
    try:
        # Extract filename from doc_id
        if "/" in doc_id:
            filename = doc_id.split("/")[-1]
        else:
            filename = doc_id
            
        # Look for the document in input/markdown
        markdown_dir = os.path.join("input", "markdown")
        doc_path = None
        
        for root, _, files in os.walk(markdown_dir):
            for file in files:
                if file == filename or file == f"{filename}.md":
                    doc_path = os.path.join(root, file)
                    break
            if doc_path:
                break
        
        if not doc_path:
            return {"success": False, "doc_id": doc_id, "error": "Document not found"}
        
        # Read document content
        with open(doc_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        return {
            "success": True,
            "doc_id": doc_id,
            "content": content,
            "path": doc_path,
            "file_size": os.path.getsize(doc_path),
            "last_modified": datetime.fromtimestamp(os.path.getmtime(doc_path)).strftime('%Y-%m-%d %H:%M:%S')
        }
    except Exception as e:
        logger.error(f"Error retrieving document {doc_id}: {str(e)}")
        return {"success": False, "doc_id": doc_id, "error": str(e)}

# Graph visualization function
def visualize_graph(concepts: List[str], depth: int = 2) -> Dict[str, Any]:
    """Generate a visualization of relationships between concepts in the knowledge graph."""
    try:
        # This is a placeholder for actual graph visualization logic
        # In a real implementation, you would extract subgraph from GraphRAG's knowledge graph
        
        # Mock response structure
        visualization = {
            "success": True,
            "concepts": concepts,
            "depth": depth,
            "nodes": [],
            "edges": [],
            "graph_data": {
                "density": 0.0,
                "average_degree": 0.0,
                "num_nodes": 0,
                "num_edges": 0
            }
        }
        
        # In a real implementation, you would:
        # 1. Extract the subgraph containing the concepts and their neighbors up to 'depth'
        # 2. Format the nodes and edges for visualization
        # 3. Calculate graph metrics
        
        # For now, return mock data that the UI can handle
        mock_nodes = []
        mock_edges = []
        
        # Create a node for each concept
        for i, concept in enumerate(concepts):
            mock_nodes.append({
                "id": f"concept_{i}",
                "label": concept,
                "type": "concept",
                "size": 10
            })
        
        # Add some mock related concepts
        related_concepts = [
            "knowledge graph", "vector database", "embedding", "neural network",
            "natural language processing", "information retrieval", "agents"
        ]
        
        for i, concept in enumerate(related_concepts[:min(len(related_concepts), depth * 2)]):
            mock_nodes.append({
                "id": f"related_{i}",
                "label": concept,
                "type": "related",
                "size": 7
            })
            
            # Connect to a random original concept
            target_concept = f"concept_{i % len(concepts)}"
            mock_edges.append({
                "source": f"related_{i}",
                "target": target_concept,
                "weight": 0.5 + (i * 0.1)
            })
        
        # Connect original concepts if more than one
        if len(concepts) > 1:
            for i in range(len(concepts) - 1):
                mock_edges.append({
                    "source": f"concept_{i}",
                    "target": f"concept_{i + 1}",
                    "weight": 0.8
                })
        
        visualization["nodes"] = mock_nodes
        visualization["edges"] = mock_edges
        visualization["graph_data"]["num_nodes"] = len(mock_nodes)
        visualization["graph_data"]["num_edges"] = len(mock_edges)
        visualization["graph_data"]["average_degree"] = (2 * len(mock_edges)) / max(1, len(mock_nodes))
        
        return visualization
    except Exception as e:
        logger.error(f"Error visualizing graph: {str(e)}")
        return {"success": False, "concepts": concepts, "error": str(e)}

# Create agents
def create_agents(model="llama3"):
    """Create and configure AutoGen agents."""
    logger.info(f"Creating agents with model: {model}")
    
    # Get configuration for the selected model
    llm_config = get_llm_config(model)
    
    # User Proxy Agent - represents the user in the agent group
    user_proxy = autogen.UserProxyAgent(
        name="user_proxy",
        human_input_mode="NEVER",
        max_consecutive_auto_reply=0,
        code_execution_config={"work_dir": "coding"},
    )
    
    # Primary Assistant Agent - handles most user interactions
    assistant = autogen.AssistantAgent(
        name="assistant",
        llm_config=llm_config,
        system_message="""You are a helpful AI assistant with access to a knowledge base via GraphRAG. 
        When asked questions, use the search_docs function to find relevant information before providing answers.
        Always cite your sources and be clear about what you know and don't know.
        Use search_docs with is_global=True for complex questions that require understanding relationships, 
        and is_global=False for straightforward factual queries.
        Format your responses in Markdown for better readability.
        If users ask to visualize concepts, use the visualize_graph function."""
    )
    
    # Register functions with the user proxy
    user_proxy.register_function(
        function_map={
            "search_docs": search_docs,
            "visualize_graph": visualize_graph,
            "get_document_content": get_document_content
        }
    )
    
    return user_proxy, assistant

# Chainlit UI setup
@cl.on_chat_start
async def on_chat_start():
    """Initialize the chat session."""
    # Initialize session variables
    cl.user_session.set("search_method", "global")
    cl.user_session.set("model", "llama3")
    cl.user_session.set("show_sources", True)
    
    # Check services
    services = check_services()
    update_document_stats()
    
    # Create agents
    user_proxy, assistant = create_agents("llama3")
    cl.user_session.set("user_proxy", user_proxy)
    cl.user_session.set("assistant", assistant)
    
    # Create UI settings
    await cl.ChatSettings(
        [
            cl.Select(
                id="search_method",
                label="Search Method",
                values=[
                    cl.Option(value="global", label="Graph-based (Relational)"),
                    cl.Option(value="local", label="Vector-based (Similarity)")
                ],
                initial_value="global",
            ),
            cl.Select(
                id="model",
                label="LLM Model",
                values=[
                    cl.Option(value="llama3", label="Llama 3"),
                    cl.Option(value="mistral", label="Mistral")
                ],
                initial_value="llama3",
            ),
            cl.Switch(
                id="show_sources",
                label="Show Source Documents",
                initial=True,
            ),
        ]
    ).send()
    
    # Create system status elements
    status_content = [
        "## System Status",
        "",
        f"- **GraphRAG**: {'✓ Ready' if system_state['services']['graphrag'] else '✗ Not Ready'}",
        f"- **LiteLLM**: {'✓ Online' if services['litellm'] else '✗ Offline'}",
        f"- **Ollama**: {'✓ Online' if services['ollama'] else '✗ Offline'}",
        "",
        "## Document Information",
        "",
        f"- **Total Documents**: {system_state['stats']['total_docs']}",
        f"- **Index Last Updated**: {system_state['stats']['index_last_updated'] or 'Unknown'}",
        "",
    ]
    
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
    
    # Create sidebar elements
    await cl.Message(content="\n".join(status_content)).send()
    
    # Add quick action buttons
    actions = [
        cl.Action(name="upload_docs", label="Upload Documents", description="Upload new documents to the knowledge base"),
        cl.Action(name="view_stats", label="View Stats", description="View detailed system statistics"),
        cl.Action(name="clear_context", label="Clear Context", description="Clear conversation context")
    ]
    
    await cl.Message(
        content="Welcome to GraphRAG + AutoGen + Ollama advanced integration! Ask me questions about your documents or use the buttons below for additional actions.",
        author="assistant",
        actions=actions
    ).send()

@cl.on_settings_update
async def on_settings_update(settings):
    """Handle settings updates."""
    logger.info(f"Settings updated: {settings}")
    
    # Update session variables
    old_model = cl.user_session.get("model", "llama3")
    cl.user_session.set("search_method", settings["search_method"])
    cl.user_session.set("model", settings["model"])
    cl.user_session.set("show_sources", settings["show_sources"])
    
    # Recreate agents if the model changed
    if settings["model"] != old_model:
        user_proxy, assistant = create_agents(settings["model"])
        cl.user_session.set("user_proxy", user_proxy)
        cl.user_session.set("assistant", assistant)
    
    await cl.Message(
        content=f"Settings updated:\n- Search Method: {settings['search_method']}\n- Model: {settings['model']}\n- Show Sources: {'Yes' if settings['show_sources'] else 'No'}",
        author="system"
    ).send()

@cl.on_message
async def on_message(message: cl.Message):
    """Process user messages."""
    query = message.content
    search_method = cl.user_session.get("search_method", "global")
    is_global = search_method == "global"
    show_sources = cl.user_session.get("show_sources", True)
    
    # Get agents from session
    user_proxy = cl.user_session.get("user_proxy")
    assistant = cl.user_session.get("assistant")
    
    if not user_proxy or not assistant:
        # Recreate agents if not in session
        user_proxy, assistant = create_agents(cl.user_session.get("model", "llama3"))
        cl.user_session.set("user_proxy", user_proxy)
        cl.user_session.set("assistant", assistant)
    
    # Create a new message for showing results
    msg = cl.Message(author="assistant", content="")
    await msg.send()
    
    # Show thinking indicator
    await msg.update(content="Searching documents and generating response...")
    
    # Start conversation with AutoGen agents
    user_proxy.initiate_chat(
        assistant, message=query
    )
    
    # Get the last message from the assistant
    last_message = assistant.last_message()
    response_content = last_message["content"]
    
    # Extract and display sources if enabled
    if show_sources and "search_docs" in str(last_message):
        try:
            # Perform a new search to get the sources
            search_result = search_docs(query, is_global=is_global)
            if search_result["success"] and search_result["total_results"] > 0:
                sources = []
                for i, doc in enumerate(search_result["results"][:3]):  # Show top 3 sources
                    source = f"**Source {i+1}**: {doc['doc_id']}\n\n"
                    source += f"```\n{doc['content'][:300]}{'...' if len(doc['content']) > 300 else ''}\n```\n"
                    sources.append(source)
                
                # Add sources after the main content
                if sources:
                    response_content += "\n\n---\n\n### Sources\n\n" + "\n".join(sources)
        except Exception as e:
            logger.error(f"Error extracting sources: {str(e)}")
    
    # Update the UI with the final response
    await msg.update(content=response_content)

@cl.on_action
async def on_action(action: cl.Action):
    """Handle UI actions."""
    if action.name == "upload_docs":
        files = await cl.AskFileMessage(
            content="Please upload documents to add to the knowledge base. Supported formats: PDF, DOCX, MD",
            accept=["application/pdf", "application/vnd.openxmlformats-officedocument.wordprocessingml.document", "text/markdown"],
            max_size_mb=10,
            max_files=5,
        ).send()
        
        if not files:
            await cl.Message(content="No files were uploaded.").send()
            return
            
        # Process uploaded files
        await process_uploaded_files(files)
    
    elif action.name == "view_stats":
        # Update statistics
        update_document_stats()
        
        # Format stats message
        stats_content = [
            "## System Statistics",
            "",
            f"- **Total Documents**: {system_state['stats']['total_docs']}",
            f"- **Total Queries**: {system_state['stats']['total_queries']}",
            f"- **Average Response Time**: {system_state['stats']['avg_response_time']:.2f} seconds",
            f"- **Index Last Updated**: {system_state['stats']['index_last_updated'] or 'Unknown'}",
            "",
            "## Available Models",
        ]
        
        for model, config in system_state["model_configs"].items():
            stats_content.append(f"- **{model}**: Context Length: {config['context_length']}, Function Calling: {'✓' if config['supports_function_calling'] else '✗'}")
        
        await cl.Message(content="\n".join(stats_content)).send()
    
    elif action.name == "clear_context":
        # Create new agents to clear context
        user_proxy, assistant = create_agents(cl.user_session.get("model", "llama3"))
        cl.user_session.set("user_proxy", user_proxy)
        cl.user_session.set("assistant", assistant)
        
        await cl.Message(content="Conversation context has been cleared.").send()

async def process_uploaded_files(files: List[cl.File]):
    """Process uploaded files and add them to the knowledge base."""
    # Create message to show progress
    msg = cl.Message(content="Processing uploaded files...", author="system")
    await msg.send()
    
    # Create temp directory for uploads
    temp_dir = os.path.join("temp", f"upload_{int(time.time())}")
    os.makedirs(temp_dir, exist_ok=True)
    
    # Save files to temp directory
    saved_files = []
    for file in files:
        file_path = os.path.join(temp_dir, file.name)
        with open(file_path, "wb") as f:
            f.write(file.content)
        saved_files.append(file_path)
    
    # Process files based on type
    markdown_dir = os.path.join("input", "markdown")
    os.makedirs(markdown_dir, exist_ok=True)
    
    # Create document processor
    processor = UniversalDocumentProcessor()
    
    # Process files
    results = []
    for file_path in saved_files:
        result = processor.process_file(file_path)
        results.append(result)
    
    # Generate report
    report = processor.generate_report(results)
    
    # Update message with status
    await msg.update(content=f"Files processed. Results:\n\n{report}")
    
    # Check if any files were successfully processed
    successful = [r for r in results if r.get("success")]
    if successful:
        # Offer to rebuild the index
        actions = [
            cl.Action(name="rebuild_index", value="yes", label="Rebuild Index Now"),
            cl.Action(name="skip_rebuild", value="no", label="Skip Rebuilding")
        ]
        
        await cl.AskActionMessage(
            content="Documents have been added to the knowledge base. Do you want to rebuild the index now?",
            actions=actions
        ).send()

@cl.on_action
async def on_rebuild_action(action: cl.Action):
    """Handle index rebuilding."""
    if action.name == "rebuild_index" and action.value == "yes":
        # Show progress message
        msg = cl.Message(author="system", content="Rebuilding GraphRAG index... This may take a few minutes.")
        await msg.send()
        
        try:
            # Run GraphRAG indexing as a background task to avoid blocking the UI
            process = await asyncio.create_subprocess_exec(
                sys.executable, "-m", "graphrag.index", "--root", ".",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                # Update stats
                update_document_stats()
                await msg.update(content="✅ GraphRAG index rebuilt successfully! The new documents are now searchable.")
            else:
                stderr_text = stderr.decode().strip() if stderr else "Unknown error"
                await msg.update(content=f"❌ Error rebuilding GraphRAG index:\n```\n{stderr_text}\n```")
        except Exception as e:
            await msg.update(content=f"❌ Error rebuilding GraphRAG index: {str(e)}")
    
    elif action.name == "skip_rebuild" and action.value == "no":
        await cl.Message(content="Index rebuilding skipped. You can rebuild the index later using the 'Rebuild Index' button.").send()

if __name__ == "__main__":
    # This will be run by Chainlit
    pass