#! /usr/bin/env python3
"""
Senior Data Scientist.: Dr. Eddy Giusepe Chirinos Isidro

Script multi_agent_langgraph_swarm_and_crewai.py
================================================
Link de estudo --> https://reference.langchain.com/python/langgraph/swarm/

DESCRIPTION:
----------
A conversational multi-agent system that combines:
    - LangGraph Swarm: Orchestration and dynamic task transfer between agents via handoff
    - CrewAI RagTool: Native tool for RAG, creates knowledge base, web page, etc (uses ChromaDB by default)
    - Tavily Search: Real-time web search

ARCHITECTURE:
------------
Two specialized agents with automatic handoff:
    - CurriculumVitaeAgent: Responds to any professional curriculum using RAG
    - SearchAgent: Searches for current information on the web

ADVANTAGES:
----------
    ✅ Specialization: each agent focuses on its expertise
    ✅ Persistence: reuses embeddings from ChromaDB without re-creating them (Azure OpenAI model to create embeddings)
    ✅ Intelligent transfer: automatic handoff between agents
    ✅ Conversational: natural and humanized responses
    ✅ Efficient RAG: semantic search on professional curriculum

DISADVANTAGES:
-------------
    ❌ Overhead of communication between agents
    ❌ Higher complexity of debug
    ❌ API costs (embedding + LLM + web search)
    ❌ Depends on multiple external services (Azure OpenAI, Tavily)
    ❌ Higher latency in handoffs between agents, since it involves re-evaluation of state and
       invocation of new agent, etc.

RUN:
    uv run multi_agent_langgraph_swarm_and_crewai.py
"""
import asyncio
import os
import sys
from pathlib import Path
from textwrap import dedent

import psycopg
from config_rag_azure import COLLECTION_NAME, rag_config
from crewai_tools import RagTool
from dotenv import find_dotenv, load_dotenv
from langchain.agents import create_agent
from langchain_core.tools import tool
from langchain_openai import AzureChatOpenAI
from langchain_tavily import TavilySearch
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langgraph_swarm import create_handoff_tool, create_swarm
from psycopg.rows import dict_row

sys.path.append(str(Path(__file__).parent.parent))
from config.ansi_colors import BLUE, CYAN, GREEN, MAGENTA, RED, RESET, YELLOW
from config.logging_config import get_logger, setup_logging

setup_logging()
logger = get_logger(__name__)


_ = load_dotenv(find_dotenv())  # read local .env file
azure_openai_api_key = os.environ["AZURE_OPENAI_API_KEY"]
azure_openai_endpoint = os.environ["AZURE_OPENAI_ENDPOINT"]
azure_apenai_api_version = os.environ["AZURE_OPENAI_API_VERSION"]
azure_openai_deployment = os.environ["AZURE_OPENAI_DEPLOYMENT"]
tavily_api_key = os.environ["TAVILY_API_KEY"]
postgres_uri = os.environ["POSTGRES_URI"]

# Path to the PDF of the curriculum (generic default name):
# User must place their curriculum in the data/:
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
    # Create RagTool once (it will get_or_create the collection internally)
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

    # Check if the collection already has data using ChromaDB API:
    try:
        chromadb_client = rag_tool.adapter._client.client
        collection = chromadb_client.get_collection(name=collection_name)
        doc_count = collection.count()

        if doc_count > 0:
            logger.info(
                f"{GREEN}✅ Collection '{collection_name}' already has {doc_count} documents. "
                f"Reusing embeddings!{RESET}"
            )
            return rag_tool
        else:
            logger.info(f"{CYAN}📋 Collection is empty. Adding data...{RESET}")
    except Exception as e:
        logger.warning(
            f"{YELLOW}⚠️ Could not check collection: {e}. Will add data to be safe.{RESET}"
        )

    # Add data only if collection is empty or check failed
    logger.info(f"{CYAN}🔄 Creating embeddings for '{pdf_path.name}'...{RESET}")
    rag_tool.add(data_type="file", path=str(pdf_path))
    logger.info(f"{GREEN}✅ Embeddings created and stored successfully!{RESET}")

    return rag_tool


# Initialize the RagTool once on module loading:
logger.info(f"{CYAN}🔄 Loading knowledge base (Curriculum)...{RESET}")
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
    api_key=azure_openai_api_key,
    api_version=azure_apenai_api_version,
    azure_endpoint=azure_openai_endpoint,
    azure_deployment=azure_openai_deployment,
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

# The workflow will be compiled inside the async main() function with the checkpointer:
workflow = create_swarm(
    agents=[curriculum_vitae_agent, search_agent],
    default_active_agent="CurriculumVitaeAgent",
)


async def main():
    """Async main function - initializes connection, checkpointer and interactive loop"""

    # Create asynchronous connection with PostgreSQL:
    logger.info(f"{CYAN}🔄 Connecting to PostgreSQL...{RESET}")
    conn = await psycopg.AsyncConnection.connect(
        postgres_uri, autocommit=True, row_factory=dict_row
    )
    logger.info(f"{GREEN}✅ Connected to PostgreSQL!{RESET}")

    # Create asynchronous checkpointer:
    checkpointer = AsyncPostgresSaver(conn)

    # Initialize PostgreSQL tables (only the first time):
    logger.info(f"{CYAN}🔄 Initializing PostgreSQL tables...{RESET}")
    await checkpointer.setup()
    logger.info(f"{GREEN}✅ Tables initialized!{RESET}")

    # Compile the workflow with the checkpointer:
    app = workflow.compile(checkpointer=checkpointer)

    config = {"configurable": {"thread_id": "1"}}

    logger.info(
        f"{YELLOW}🤖 Multi-Agent System for Curriculum Analysis (RAG) and Web Search 🤖{RESET}"
    )
    logger.info(f"{CYAN}Enter 'exit', 'quit' or 'q' to exit.{RESET}")

    agent_display = {
        "CurriculumVitaeAgent": f"{MAGENTA}📄 CurriculumVitaeAgent (Curriculum Analysis){RESET}",
        "SearchAgent": f"{BLUE}🌐 SearchAgent (Web Search){RESET}",
    }

    try:
        while True:
            try:
                question = input(f"{RED}💬 Your question: {RESET}").strip()

                if question.lower() in ["exit", "quit", "q"]:
                    logger.info(f"{RED}👋 Closing... See you later!{RESET}")
                    break

                if not question:
                    logger.warning(f"{RED}⚠️  Please enter a valid question.{RESET}")
                    continue

                # Use ainvoke instead of invoke:
                result = await app.ainvoke(
                    {"messages": [{"role": "user", "content": question}]}, config
                )
                message = result["messages"][-1]
                agent = getattr(message, "name", "Unknown")

                print(agent_display.get(agent, f"{YELLOW}🤖 {agent}{RESET}"))
                print(f"{GREEN}💬 {message.content.strip()}{RESET}\n")

            except KeyboardInterrupt:
                logger.info(f"{GREEN}👋 Closing... See you later!{RESET}")
                break
            except Exception as e:
                logger.error(f"{RED}❌ Error processing: {e}. Try again.{RESET}")
    finally:
        # Close connection when exiting:
        logger.info(f"{CYAN}🔄 Closing connection with PostgreSQL...{RESET}")
        await conn.close()
        logger.info(f"{GREEN}✅ Connection closed!{RESET}")


if __name__ == "__main__":
    # Run main async loop:
    asyncio.run(main())
