#!/usr/bin/env python3
"""
Script view_collections.py
==========================
This script is used to view the collections of the ChromaDB.

RUN
---
  uv run view_collections.py
"""
import subprocess
import sys
from pathlib import Path

import chromadb

# Add parent directory to path for imports:
sys.path.insert(0, str(Path(__file__).parent.parent))
from config.logging_config import get_logger, setup_logging

# Initialize logging:
setup_logging()
logger = get_logger(__name__)


# Path where the CrewAI saves the data:
CHROMA_PATH = Path.home() / ".local/share/example1_langgraph_swarm"

logger.info("🗂️ COLLECTIONS OF CHROMADB")
logger.info(f"\n📁 Location: {CHROMA_PATH}")
# print("Total size: ", end="")


result = subprocess.run(
    ["du", "-sh", str(CHROMA_PATH)], capture_output=True, text=True, check=True
)
logger.info(f"Total size: {result.stdout.split()[0]}")

# Connect to ChromaDB:
client = chromadb.PersistentClient(path=str(CHROMA_PATH))
collections = client.list_collections()

logger.info(f"\n📊 Total number of collections: {len(collections)}\n")

for i, col in enumerate(collections, 1):
    logger.info(f'{i}. 📁 Collection: "{col.name}"')
    logger.info(f"   └─ UUID: {col.id}")
    logger.info(f"   └─ Documents/Chunks: {col.count()}")

    if col.count() > 0:
        # Get a sample of the data:
        result = col.peek(limit=1)
        if result["metadatas"] and result["metadatas"][0]:
            logger.info("   └─ Sample metadata:")
            for key, value in list(result["metadatas"][0].items())[:3]:
                value_str = (
                    str(value)[:50] + "..." if len(str(value)) > 50 else str(value)
                )
                logger.info(f"      • {key}: {value_str}")
