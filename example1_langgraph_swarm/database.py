#! /usr/bin/env python3
"""
Senior Data Scientist.: Dr. Eddy Giusepe Chirinos Isidro

Script database.py
==================
This script provides a PostgreSQL connection management with async
context manager.
It provides a clean way to manage the database connection lifecycle,
ensuring proper cleanup even when exceptions occur.
"""
import sys
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from pathlib import Path

import psycopg
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from psycopg.rows import dict_row

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from config.logging_config import get_logger, setup_logging

# Initialize logging:
setup_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def get_checkpointer(uri: str) -> AsyncGenerator[AsyncPostgresSaver]:
    """
    Async context manager for PostgreSQL connection with checkpointer.

    Handles connection lifecycle automatically:
    - Opens connection on enter
    - Sets up checkpointer tables if needed
    - Closes connection on exit (even if exception occurs)

    Args:
        uri: PostgreSQL connection URI (e.g., postgresql://user:pass@host:port/db)

    Yields:
        AsyncPostgresSaver: Configured checkpointer ready for use

    Example:
        async with get_checkpointer(postgres_uri) as checkpointer:
            app = workflow.compile(checkpointer=checkpointer)
    """
    logger.info("Connecting to PostgreSQL...")
    conn = await psycopg.AsyncConnection.connect(
        uri, autocommit=True, row_factory=dict_row
    )

    try:
        checkpointer = AsyncPostgresSaver(conn)
        await checkpointer.setup()
        logger.info("Connected to PostgreSQL and checkpointer ready")
        yield checkpointer
    finally:
        logger.info("Closing PostgreSQL connection...")
        await conn.close()
        logger.info("PostgreSQL connection closed")
