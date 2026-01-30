#! /usr/bin/env python3
"""
Senior Data Scientist.: Dr. Eddy Giusepe Chirinos Isidro

Script config_rag_azure.py
==========================
This module provides the necessary configurations for integration of a RAG system
using Azure OpenAI as embedding provider and ChromaDB as vector database for
document storage and retrieval.

The system is designed to work with professional documents (curricula, portfolios, etc.)
and allows efficient reuse of embeddings through a persistent collection in ChromaDB.

Main Dependencies:
- crewai_tools: Framework for AI agent tools
- chromadb: Vector database for embedding storage
- azure-openai: Azure embedding model service
"""
import os

from crewai_tools.tools.rag import (
    ProviderSpec,
    RagToolConfig,
    VectorDbConfig,
)
from dotenv import find_dotenv, load_dotenv

_ = load_dotenv(find_dotenv()) # read local .env file

# Name of the collection (MUST be the same to reuse embeddings!)
# Generic name to work with any professional curriculum
COLLECTION_NAME = "rag_cv_professional_langgraph"

# Configuration of the VectorDB (ChromaDB with persistence):
vectordb: VectorDbConfig = {
    "provider": "chromadb",
    "config": {
        "collection_name": COLLECTION_NAME,
    },
}

# Configuration of the embedding model (Azure OpenAI):
embedding_model: ProviderSpec = {
    "provider": "azure",
    "config": {
        "deployment_id": os.environ.get("AZURE_OPENAI_EMBED_DEPLOYMENT_LARGE"),
        "api_key": os.environ.get("AZURE_OPENAI_API_KEY"),
        "api_base": os.environ.get("AZURE_OPENAI_ENDPOINT"),
        "api_version": os.environ.get("AZURE_OPENAI_API_VERSION"),
    },
}

# Complete configuration of the RAG Tool:
rag_config: RagToolConfig = {
    "vectordb": vectordb,
    "embedding_model": embedding_model,
}
