#! /usr/bin/env python3
"""
Senior Data Scientist.: Dr. Eddy Giusepe Chirinos Isidro

Script api.py
=============
FastAPI Application for the multi-agent system.

Provides REST API Endpoints for:
    - POST /chat: Process questions through the multi-agent system
    - GET /health: Health check endpoint

The API manages the PostgreSQL connection lifecycle automatically
using FastAPI's lifespan context manager.

Run with:
    uvicorn example1_langgraph_swarm.api:app --reload --port 8000

or inside from directory:
    uvicorn api:app --reload --port 8000
"""
import sys
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

# Add parent directory to path for imports:
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents import create_app
from database import get_checkpointer
from service import ChatResponse, process_question

from config.ansi_colors import GREEN, RED, RESET, YELLOW
from config.logging_config import get_logger, setup_logging
from config.settings import POSTGRES_URI

# Initialize logging:
setup_logging()
logger = get_logger(__name__)


class ChatRequest(BaseModel):
    """Request model for the /chat endpoint."""

    question: str = Field(
        ...,
        min_length=2,
        description="The question to ask the multi-agent system",
        examples=["What programming languages does the candidate know?"],
    )
    thread_id: str = Field(
        ...,
        min_length=1,
        description="Unique session/thread ID for conversation continuity",
        examples=["user-session-abc123"],
    )


class HealthResponse(BaseModel):
    """Response model for the /health endpoint."""

    status: str = Field(description="Health status of the API")
    message: str = Field(description="Additional health information")


class AppState:
    """Container for application state to avoid global variables."""

    def __init__(self):
        """Initialize the application state."""
        self.app_instance: Any = None
        self.checkpointer_cm: Any = None


app_state = AppState()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manage application lifecycle.

    On startup:
        - Connect to PostgreSQL
        - Initialize checkpointer
        - Compile workflow

    On shutdown:
        - Close PostgreSQL connection
    """
    logger.info(f"{GREEN}Starting API - connecting to PostgreSQL...{RESET}")

    # Enter the context manager manually to keep connection open
    app_state.checkpointer_cm = get_checkpointer(POSTGRES_URI)
    checkpointer = await app_state.checkpointer_cm.__aenter__()
    app_state.app_instance = create_app(checkpointer)

    logger.info(f"{YELLOW}API ready - workflow compiled{RESET}")

    yield

    # Cleanup on shutdown:
    logger.info(f"{RED}Shutting down API...{RESET}")
    await app_state.checkpointer_cm.__aexit__(None, None, None)
    logger.info(f"{RED}API shutdown complete{RESET}")


app = FastAPI(
    title="Multi-Agent Curriculum API",
    description="""
API for a multi-agent system that combines:
- **CurriculumVitaeAgent**: Analyzes professional curricula using RAG
- **SearchAgent**: Searches the web for current information

The agents automatically hand off to each other based on the question type.
    """,
    version="1.0.0",
    lifespan=lifespan,
)


@app.post("/chat", response_model=ChatResponse, tags=["Chat"])
async def chat(request: ChatRequest) -> ChatResponse:
    """
    Process a question through the multi-agent system.

    The system will automatically route the question to the appropriate agent:
    - Questions about the curriculum → CurriculumVitaeAgent
    - Questions about current events, news, etc. → SearchAgent

    **thread_id**: Use the same thread_id for conversation continuity.
    Each unique thread_id maintains its own conversation history.
    """
    if app_state.app_instance is None:
        raise HTTPException(
            status_code=503,
            detail="Service not ready - workflow not initialized",
        )

    try:
        response = await process_question(
            app=app_state.app_instance,
            question=request.question,
            thread_id=request.thread_id,
        )
        return response
    except Exception as e:
        logger.error(f"{RED}Error processing question: {e}{RESET}")
        raise HTTPException(
            status_code=500,
            detail=f"Error processing question: {e!s}",
        ) from e


@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health() -> HealthResponse:
    """
    Health check endpoint.

    Returns the current status of the API and its components.
    """
    if app_state.app_instance is None:
        return HealthResponse(
            status="degraded",
            message="Workflow not initialized",
        )

    return HealthResponse(
        status="healthy",
        message="API is running and workflow is ready",
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)
