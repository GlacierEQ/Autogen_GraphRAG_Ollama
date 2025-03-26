# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""OpenAI Embedding model implementation."""

import asyncio
from collections.abc import Callable
from typing import Any
import ollama
import numpy as np
import tiktoken
from tenacity import (
    AsyncRetrying,
    RetryError,
    Retrying,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential_jitter,
)

from graphrag.query.llm.base import BaseTextEmbedding
from graphrag.query.llm.oai.base import OpenAILLMImpl
from graphrag.query.llm.oai.typing import (
    OPENAI_RETRY_ERROR_TYPES,
    OpenaiApiType,
)
from graphrag.query.llm.text_utils import chunk_text
from graphrag.query.progress import StatusReporter

"""This file extends GraphRAG's embedding functionality to work with local Ollama models."""

import json
from typing import Any, Dict, List, Union, cast

from graphrag.query.llm.oai.base import OpenAIOracleConfig
import requests

class OllamaEmbedding:
    """Ollama embedding class using local embedding models."""
    
    def __init__(self, config: OpenAIOracleConfig):
        """Initialize the Ollama embedding."""
        self.model = config.model_name
        self.api_base = "http://localhost:11434/api/embeddings"
    
    def get_text_embedding(self, text: str) -> List[float]:
        """Get text embedding from Ollama."""
        payload = {
            "model": self.model,
            "prompt": text
        }
        
        response = requests.post(self.api_base, json=payload)
        if response.status_code != 200:
            raise ValueError(f"Failed to get embedding: {response.text}")
        
        return response.json()["embedding"]
    
    def get_text_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Get text embeddings from Ollama."""
        embeddings = []
        for text in texts:
            embedding = self.get_text_embedding(text)
            embeddings.append(embedding)
        return embeddings

def embedding_factory(
    config: OpenAIOracleConfig,
) -> Union[Any, OllamaEmbedding]:
    """Create embedding object based on provider."""
    if config.provider == "local_ollama":
        return OllamaEmbedding(config)
    else:
        # Use original factory method for other providers
        from graphrag.query.llm.oai.embedding_original import embedding_factory as original_factory
        return original_factory(config)

class OpenAIEmbedding(BaseTextEmbedding, OpenAILLMImpl):
    """Wrapper for OpenAI Embedding models."""

    def __init__(
        self,
        api_key: str | None = None,
        azure_ad_token_provider: Callable | None = None,
        model: str = "text-embedding-3-small",
        deployment_name: str | None = None,
        api_base: str | None = None,
        api_version: str | None = None,
        api_type: OpenaiApiType = OpenaiApiType.OpenAI,
        organization: str | None = None,
        encoding_name: str = "cl100k_base",
        max_tokens: int = 8191,
        max_retries: int = 10,
        request_timeout: float = 180.0,
        retry_error_types: tuple[type[BaseException]] = OPENAI_RETRY_ERROR_TYPES,  # type: ignore
        reporter: StatusReporter | None = None,
    ):
        OpenAILLMImpl.__init__(
            self=self,
            api_key=api_key,
            azure_ad_token_provider=azure_ad_token_provider,
            deployment_name=deployment_name,
            api_base=api_base,
            api_version=api_version,
            api_type=api_type,  # type: ignore
            organization=organization,
            max_retries=max_retries,
            request_timeout=request_timeout,
            reporter=reporter,
        )

        self.model = model
        self.encoding_name = encoding_name
        self.max_tokens = max_tokens
        self.token_encoder = tiktoken.get_encoding(self.encoding_name)
        self.retry_error_types = retry_error_types
        self.embedding_dim = 384  # Nomic-embed-text model dimension
        self.ollama_client = ollama.Client()

    def embed(self, text: str, **kwargs: Any) -> list[float]:
        """Embed text using Ollama's nomic-embed-text model."""
        try:
            embedding = self.ollama_client.embeddings(model="nomic-embed-text", prompt=text)
            return embedding["embedding"]
        except Exception as e:
            self._reporter.error(
                message="Error embedding text",
                details={self.__class__.__name__: str(e)},
            )
            return np.zeros(self.embedding_dim).tolist()

    async def aembed(self, text: str, **kwargs: Any) -> list[float]:
        """Embed text using Ollama's nomic-embed-text model asynchronously."""
        try:
            embedding = await self.ollama_client.embeddings(model="nomic-embed-text", prompt=text)
            return embedding["embedding"]
        except Exception as e:
            self._reporter.error(
                message="Error embedding text asynchronously",
                details={self.__class__.__name__: str(e)},
            )
            return np.zeros(self.embedding_dim).tolist()

    def _embed_with_retry(
        self, text: str | tuple, **kwargs: Any  #str | tuple
    ) -> tuple[list[float], int]:
        try:
            retryer = Retrying(
                stop=stop_after_attempt(self.max_retries),
                wait=wait_exponential_jitter(max=10),
                reraise=True,
                retry=retry_if_exception_type(self.retry_error_types),
            )
            for attempt in retryer:
                with attempt:
                    embedding = (
                        self.sync_client.embeddings.create(  # type: ignore
                            input=text,
                            model=self.model,
                            **kwargs,  # type: ignore
                        )
                        .data[0]
                        .embedding
                        or []
                    )  
                    return (embedding["embedding"], len(text))
        except RetryError as e:
            self._reporter.error(
                message="Error at embed_with_retry()",
                details={self.__class__.__name__: str(e)},
            )
            return ([], 0)
        else:
            # TODO: why not just throw in this case?
            return ([], 0)

    async def _aembed_with_retry(
        self, text: str | tuple, **kwargs: Any
    ) -> tuple[list[float], int]:
        try:
            retryer = AsyncRetrying(
                stop=stop_after_attempt(self.max_retries),
                wait=wait_exponential_jitter(max=10),
                reraise=True,
                retry=retry_if_exception_type(self.retry_error_types),
            )
            async for attempt in retryer:
                with attempt:
                    embedding = (
                        await self.async_client.embeddings.create(  # type: ignore
                            input=text,
                            model=self.model,
                            **kwargs,  # type: ignore
                        )
                    ).data[0].embedding or []
                    return (embedding, len(text))
        except RetryError as e:
            self._reporter.error(
                message="Error at embed_with_retry()",
                details={self.__class__.__name__: str(e)},
            )
            return ([], 0)
        else:
            # TODO: why not just throw in this case?
            return ([], 0)
