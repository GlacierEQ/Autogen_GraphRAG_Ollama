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
    """Check if required services are