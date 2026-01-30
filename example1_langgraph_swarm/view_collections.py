#!/usr/bin/env python3
"""
Script para visualizar as collections do ChromaDB.

Uso:
    uv run view_collections.py
"""
import subprocess
from pathlib import Path

import chromadb

# Caminho onde o CrewAI salva os dados
CHROMA_PATH = Path.home() / ".local/share/example1_langgraph_swarm"

print("\n" + "="*70)
print("🗂️  COLLECTIONS DO CHROMADB")
print("="*70)

print(f"\n📁 Localização: {CHROMA_PATH}")
print("   Tamanho total: ", end="")


result = subprocess.run(['du', '-sh', str(CHROMA_PATH)], capture_output=True, text=True, check=True)
print(result.stdout.split()[0])

# Conectar ao ChromaDB
client = chromadb.PersistentClient(path=str(CHROMA_PATH))
collections = client.list_collections()

print(f"\n📊 Total de collections: {len(collections)}\n")

for i, col in enumerate(collections, 1):
    print(f"{i}. 📁 Collection: \"{col.name}\"")
    print(f"   └─ UUID: {col.id}")
    print(f"   └─ Documentos/Chunks: {col.count()}")

    if col.count() > 0:
        # Pegar uma amostra dos dados
        result = col.peek(limit=1)
        if result['metadatas'] and result['metadatas'][0]:
            print("   └─ Metadados de exemplo:")
            for key, value in list(result['metadatas'][0].items())[:3]:
                value_str = str(value)[:50] + "..." if len(str(value)) > 50 else str(value)
                print(f"      • {key}: {value_str}")
    print()

print("="*70)
print("💡 Para deletar uma collection:")
print("   uv run python -c \"import chromadb; ")
print(f"   client = chromadb.PersistentClient(path='{CHROMA_PATH}'); ")
print("   client.delete_collection('nome_da_collection')\"")
print("="*70 + "\n")
