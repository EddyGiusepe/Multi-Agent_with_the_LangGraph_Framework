#! /usr/bin/env python3
"""
Senior Data Scientist.: Dr. Eddy Giusepe Chirinos Isidro

Module agents.py
================
Agent definitions and workflow creation for the multi-agent system.

This module contains:
    - RAG tool for curriculum analysis (using CrewAI RagTool + Azure OpenAI embeddings)
    - Web search tool (using Tavily)
    - Two specialized agents: CurriculumVitaeAgent and SearchAgent
    - Workflow creation with automatic handoff between agents

Usage:
    from example1_langgraph_swarm.agents import create_app, workflow

    app = create_app(checkpointer)
    result = await app.ainvoke({"messages": [...]}, config)
"""
import sys
from pathlib import Path
from textwrap import dedent
from typing import TYPE_CHECKING

from config_rag_azure import COLLECTION_NAME, rag_config
from crewai_tools import RagTool
from langchain.agents import create_agent
from langchain_core.tools import tool
from langchain_openai import AzureChatOpenAI
from langchain_tavily import TavilySearch
from langgraph_swarm import create_handoff_tool, create_swarm

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from config.ansi_colors import CYAN, GREEN, RESET, YELLOW
from config.logging_config import get_logger
from config.settings import (
    AZURE_OPENAI_API_KEY,
    AZURE_OPENAI_API_VERSION,
    AZURE_OPENAI_DEPLOYMENT,
    AZURE_OPENAI_ENDPOINT,
)

# TYPE_CHECKING: imports apenas para type hints (não executados em runtime)
# Isso evita carregar módulos desnecessários quando só precisamos das anotações de tipo
if TYPE_CHECKING:
    from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
    from langgraph.graph.state import CompiledStateGraph

logger = get_logger(__name__)

PDF_PATH = Path(__file__).parent / "data" / "Data_Science_Eddy_en.pdf"


def load_rag_tool(
    pdf_path: Path,
    collection_name: str = COLLECTION_NAME,
    limit: int = 7,
    similarity_threshold: float = 0.50,
) -> RagTool:
    """
    Load the RagTool with persistence check.

    If the collection already exists in ChromaDB, do not recreate the embeddings!
    This saves time and API costs.

    Args:
        pdf_path: Path to the PDF file
        collection_name: Name of the collection in ChromaDB
        limit: Number of chunks retrieved
        similarity_threshold: Similarity threshold for retrieval

    Returns:
        RagTool configured and loaded with the PDF
    """
    # Create RagTool once (it will get_or_create the collection internally):
    rag_tool = RagTool(
        name="Professional Curriculum Knowledge Base",
        description=dedent(
            """Knowledge base to answer questions about the professional
               curriculum of the candidate.
            """
        ),
        limit=limit,
        similarity_threshold=similarity_threshold,
        collection_name=collection_name,
        config=rag_config,
        summarize=True,
    )

    # Check if collection already has data using ChromaDB API
    try:
        chromadb_client = rag_tool.adapter._client.client
        collection = chromadb_client.get_collection(name=collection_name)
        doc_count = collection.count()

        if doc_count > 0:
            logger.info(
                f"{GREEN}Collection '{collection_name}' already has {doc_count} documents. "
                f"Reusing embeddings!{RESET}"
            )
            return rag_tool
        else:
            logger.info(f"{CYAN}Collection is empty. Adding data...{RESET}")
    except Exception as e:
        logger.warning(
            f"{YELLOW}⚠️ Could not check collection: {e}. Will add data to be safe.{RESET}"
        )

    # Add data only if collection is empty or check failed
    logger.info(f"{CYAN}Creating embeddings for '{pdf_path.name}'...{RESET}")
    rag_tool.add(data_type="file", path=str(pdf_path))
    logger.info(f"{GREEN}Embeddings created and stored successfully!{RESET}")

    return rag_tool


# ==================================================
# Initialize RAG Tool (loaded once on module import)
# ==================================================
logger.info(f"{CYAN}Loading knowledge base (Curriculum)...{RESET}")
_rag_tool = load_rag_tool(PDF_PATH)


@tool
def cv_knowledge_base(query: str) -> str:
    """Search in the knowledge base of the professional curriculum.

    Use this tool to answer questions about:
    - Professional experience of the candidate
    - Technical and soft skills
    - Academic formation
    - Projects performed
    - Certifications and courses
    - Languages
    """
    return _rag_tool.run(query)


web_search_tool = TavilySearch(
    max_results=5,  # Increase number of results
    search_depth="advanced",  # Use advanced search
    include_answer=True,  # Include summary of the answer
    include_raw_content=False,
    include_images=False,
)


model = AzureChatOpenAI(
    api_key=AZURE_OPENAI_API_KEY,
    api_version=AZURE_OPENAI_API_VERSION,
    azure_endpoint=AZURE_OPENAI_ENDPOINT,
    azure_deployment=AZURE_OPENAI_DEPLOYMENT,
)


curriculum_vitae_agent = create_agent(
    model=model,
    tools=[
        cv_knowledge_base,
        create_handoff_tool(
            agent_name="SearchAgent",
            description=dedent(
                """MUST use this tool to transfer to SearchAgent when:
                - The question is NOT about the professional curriculum
                - Questions about politics, presidents, elections
                - Questions about news, current events
                - Questions about technologies, products, companies
                - Any question that needs information from the internet
                - Any question that you cannot answer based only on the curriculum
            """
            ),
        ),
    ],
    system_prompt=dedent(
        """
    You are an assistant specialized in analyzing professional curricula.

    SCOPE - YOU RESPOND ONLY ABOUT THE CURRICULUM:
    - Professional experience
    - Technical and soft skills
    - Academic formation
    - Projects performed
    - Certifications and courses
    - Languages

    NATURAL AND HUMANIZED RESPONSES:
    - Respond as if you were a person who knows the professional curriculum well
    - DO NOT mention where you found the information (section, document, database, top, part)
    - DO NOT use technical phrases like "found in the section", "according to the document", "extracted from the top"
    - Be conversational and direct, like a colleague explaining about the curriculum
    - If you cannot find information, say: "I did not find information about that subject in the curriculum."

    EXAMPLES OF RESPONSES:
    ❌ WRONG (robotized): "According to the document, the professional worked with Python..."
    ✅ CORRECT (humanized): "The professional worked with Python..."

    ❌ WRONG (robotized): "In the experience section, I found that he..."
    ✅ CORRECT (humanized): "He worked..."

    TRANSFER TO SearchAgent:
    Transfer immediately to SearchAgent when the question is about:
    - Politics, news, current events
    - Technologies, products, companies (current internet information)
    - ANYTHING that is NOT in the professional curriculum

    Always respond in English.
    """
    ),
    name="CurriculumVitaeAgent",
)

search_agent = create_agent(
    model=model,
    tools=[
        web_search_tool,
        create_handoff_tool(
            agent_name="CurriculumVitaeAgent",
            description=dedent(
                """Transfer to CurriculumVitaeAgent when:
                - The user asks about the professional curriculum/CV
                - Questions about professional experience of the candidate
                - Questions about technical and soft skills, academic formation, projects of the professional
            """
            ),
        ),
    ],
    system_prompt=dedent(
        """
    You are the SearchAgent, an assistant that searches the internet.

    REQUIRED RULE: You MUST ALWAYS use the tavily_search tool to
    search information BEFORE answering any question.
    NEVER answer using only your internal knowledge - always search first!

    Your responsibilities:
    1. Receive questions about current information (news, politics, technology, etc.)
    2. Use the tavily_search tool to search the internet
    3. Answer based on the search results
    4. If the user asks about the professional curriculum/CV, transfer to CurriculumVitaeAgent

    Always respond in English.
    """
    ),
    name="SearchAgent",
)


workflow = create_swarm(
    agents=[curriculum_vitae_agent, search_agent],
    default_active_agent="CurriculumVitaeAgent",
)


def create_app(checkpointer: "AsyncPostgresSaver") -> "CompiledStateGraph":
    """
    Compile the workflow with the given checkpointer.

    Args:
        checkpointer: AsyncPostgresSaver instance for state persistence

    Returns:
        CompiledStateGraph ready to process messages
    """
    return workflow.compile(checkpointer=checkpointer)
