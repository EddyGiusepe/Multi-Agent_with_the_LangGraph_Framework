#! /usr/bin/env python3
"""
Senior Data Scientist.: Dr. Eddy Giusepe Chirinos Isidro

Script cli.py
=============
Interactive CLI for the multi-agent system.
Provides a REPL (Read-Eval-Print-Loop) interface for testing
and interacting with the multi-agent system from the terminal.

Run
    uv run cli.py
"""
import asyncio
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents import create_app
from database import get_checkpointer
from service import process_question

from config.ansi_colors import BLUE, CYAN, GREEN, MAGENTA, RED, RESET, YELLOW
from config.logging_config import get_logger, setup_logging
from config.settings import POSTGRES_URI

# Initialize logging
setup_logging()
logger = get_logger(__name__)


# =====================
# Display Configuration
# =====================
AGENT_DISPLAY = {
    "CurriculumVitaeAgent": f"{MAGENTA}📄 CurriculumVitaeAgent (Curriculum Analysis){RESET}",
    "SearchAgent": f"{BLUE}🌐 SearchAgent (Web Search){RESET}",
}


# ================
# Interactive Loop
# ================
async def run_interactive_loop(app, thread_id: str = "cli-session") -> None:
    """
    Run the interactive REPL loop.

    Args:
        app: Compiled LangGraph workflow
        thread_id: Thread identifier for this CLI session
    """
    logger.info(
        f"{YELLOW}🤖 Multi-Agent System for Curriculum Analysis (RAG) and Web Search 🤖{RESET}"
    )
    logger.info(f"{CYAN}Enter 'exit', 'quit' or 'q' to exit.{RESET}")

    while True:
        try:
            question = input(f"{RED}💬 Your question: {RESET}").strip()

            if question.lower() in ["exit", "quit", "q"]:
                logger.info(f"{RED}👋 Closing... See you later!{RESET}")
                break

            if not question:
                logger.warning(f"{RED}⚠️  Please enter a valid question.{RESET}")
                continue

            response = await process_question(app, question, thread_id)
            agent_label = AGENT_DISPLAY.get(
                response.agent_name, f"{YELLOW}🤖 {response.agent_name}{RESET}"
            )
            print(agent_label)
            print(f"{GREEN}💬 {response.content}{RESET}\n")

        except KeyboardInterrupt:
            logger.info(f"{GREEN}👋 Closing... See you later!{RESET}")
            break
        except Exception as e:
            logger.error(f"{RED}❌ Error processing: {e}. Try again.{RESET}")


# ================
# Main Entry Point
# ================
async def main() -> None:
    """
    Main entry point for the CLI.

    Manages the PostgreSQL connection lifecycle and runs the interactive loop.
    """
    async with get_checkpointer(POSTGRES_URI) as checkpointer:
        app = create_app(checkpointer)
        await run_interactive_loop(app)


if __name__ == "__main__":
    asyncio.run(main())
