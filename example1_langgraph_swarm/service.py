#! /usr/bin/env python3
"""
Senior Data Scientist.: Dr. Eddy Giusepe Chirinos Isidro

Script service.py
=================
This script provides the business logic for processing questions in the
multi-agent system.

This script is the core of the application, containing the reusable logic
that can be used by both CLI and API.

Key components:
    - ChatResponse: Pydantic model for structured responses
    - process_question: Main function to process user questions
"""
from typing import TYPE_CHECKING

from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from langgraph.graph.state import CompiledStateGraph


class ChatResponse(BaseModel):
    """
    Structured response from the multi-agent chat system.

    This model is used both internally and as FastAPI response_model,
    ensuring consistency across the application.

    Attributes:
        agent_name: Name of the agent that generated the response
        content: The actual response content
        thread_id: Session/thread identifier for conversation continuity
    """

    agent_name: str = Field(description="Name of the agent that responded")
    content: str = Field(description="Response content from the agent")
    thread_id: str = Field(description="Thread/session identifier")


async def process_question(
    app: "CompiledStateGraph",
    question: str,
    thread_id: str,
) -> ChatResponse:
    """
    Process a question through the multi-agent system.

    This is the main business logic function that:
    1. Configures the thread for conversation continuity
    2. Invokes the compiled workflow
    3. Extracts and returns the structured response

    Args:
        app: Compiled LangGraph workflow with checkpointer
        question: User's question to process
        thread_id: Unique identifier for the conversation thread.
                   Each user/session should have a unique thread_id
                   to maintain conversation history.

    Returns:
        ChatResponse with agent name, content, and thread_id

    Example:
        async with get_checkpointer(postgres_uri) as checkpointer:
            app = create_app(checkpointer)
            response = await process_question(
                app,
                "What programming languages does the candidate know?",
                "user-session-abc123"
            )
            print(f"{response.agent_name}: {response.content}")
    """
    config = {"configurable": {"thread_id": thread_id}}

    result = await app.ainvoke(
        {"messages": [{"role": "user", "content": question}]},
        config,
    )

    message = result["messages"][-1]

    return ChatResponse(
        agent_name=getattr(message, "name", "Unknown"),
        content=message.content.strip(),
        thread_id=thread_id,
    )
