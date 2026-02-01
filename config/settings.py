#! /usr/bin/env python3
"""
Senior Data Scientist.: Dr. Eddy Giusepe Chirinos Isidro

Script settings.py
==================
Este script contém as configurações centralizadas para o projeto.
Todas as variáveis de ambiente são carregadas aqui para reutilização em módulos.
"""
import os
from pathlib import Path

from dotenv import find_dotenv, load_dotenv

# Project root directory:
PROJECT_ROOT = Path(__file__).parent.parent

_ = load_dotenv(find_dotenv())  # read local .env file

# =====================================
# OpenAI / Anthropic / Mistral / Google
# =====================================
OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]
ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"]
MISTRALAI_API_KEY = os.environ["MISTRALAI_API_KEY"]
EXA_API_KEY = os.environ["EXA_API_KEY"]
GOOGLE_API_KEY = os.environ["GOOGLE_API_KEY"]
# GOOGLE_SEARCH_API_KEY = os.environ["GOOGLE_SEARCH_API_KEY"]
# SEARCH_ENGINE_ID = os.environ["SEARCH_ENGINE_ID"]
MCP_SERVER_URL = os.environ["MCP_SERVER_URL"]

# =============================================
# Azure OpenAI (used by LangGraph Swarm agents)
# =============================================
AZURE_OPENAI_API_KEY = os.environ["AZURE_OPENAI_API_KEY"]
AZURE_OPENAI_ENDPOINT = os.environ["AZURE_OPENAI_ENDPOINT"]
AZURE_OPENAI_API_VERSION = os.environ["AZURE_OPENAI_API_VERSION"]
AZURE_OPENAI_DEPLOYMENT = os.environ["AZURE_OPENAI_DEPLOYMENT"]

# ===================
# Tavily (web search)
# ===================
TAVILY_API_KEY = os.environ["TAVILY_API_KEY"]

# ===================================
# PostgreSQL (LangGraph checkpointer)
# ===================================
POSTGRES_URI = os.environ["POSTGRES_URI"]
