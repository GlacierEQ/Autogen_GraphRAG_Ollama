# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""This file extends GraphRAG's embedding functionality to work with local Ollama models."""

import json
import logging
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple, cast

import requests
from graphrag.llm.base import LLMBase, ModelBase
from graphrag.llm.openai.openai_base import OpenAIBase, OpenAIConfig

logger = logging.getLogger(__name__)

@dataclass
class OpenAIEmbeddingsConfig(OpenAIConfig):
    """OpenAI embeddings config."""
    dimension: Optional[int] = None


class OpenAIEmbeddingsLLM(OpenAIBase):
    """OpenAI embeddings LLM."""

    def __init__(self, config: OpenAIEmbeddingsConfig):
        """Initialize the OpenAI embeddings LLM."""
        super().__init__(config)
        self.dimension = config.dimension

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Embed documents with OpenAI."""
        if len(texts) == 0:
            return []
        
        # Handle local Ollama model
        if self.config.provider == "local_ollama":
            return self._embed_documents_ollama(texts)
            
        # Original OpenAI embedding logic
        # ...existing code...
        
    def _embed_documents_ollama(self, texts: List[str]) -> List[List[float]]:
        """Embed documents with local Ollama."""
        embeddings = []
        api_url = "http://localhost:11434/api/embeddings"
        
        for text in texts:
            payload = {
                "model": self.config.model_name,
                "prompt": text
            }
            
            try:
                response = requests.post(api_url, json=payload)
                response.raise_for_status()
                embedding = response.json()["embedding"]
                embeddings.append(embedding)
            except Exception as e:
                logger.error(f"Error getting embedding from Ollama: {e}")
                # Return zero vector as fallback
                if self.dimension:
                    embeddings.append([0.0] * self.dimension)
                else:
                    # Default to a reasonable dimension if not specified
                    embeddings.append([0.0] * 768)
            
            # Brief pause to avoid overloading the API
            time.sleep(0.1)
        
        return embeddings
