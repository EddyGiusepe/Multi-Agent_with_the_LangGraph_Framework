"""
Senior Data Scientist.: Dr. Eddy Giusepe Chirinos Isidro

Script ui.py
============
Multi-Agent UI Frontend - ReactPy Interface

This is a pure frontend application that consumes the multi-agent API.

Prerequisites:
==============
1. PostgreSQL running (docker-compose up -d)
2. API Backend running on port 8000:
   uvicorn example1_langgraph_swarm.api:app --reload --port 8000

Run UI:
=======
uv run example1_langgraph_swarm/ui_reactpy/ui.py

Access:
=======
UI: http://localhost:8080
API: http://localhost:8000 (backend)
"""

import uuid

import httpx
import uvicorn
from fastapi import FastAPI
from reactpy import component, hooks, html
from reactpy.backend.fastapi import configure

# =======================
# CSS STYLES (Dark Theme)
# =======================
COLORS = {
    "background": "#1a1a2e",
    "card": "#16213e",
    "accent": "#0f3460",
    "primary": "#e94560",
    "primary_hover": "#ff6b6b",
    "text": "#eaeaea",
    "text_muted": "#a0a0a0",
    "user_bubble": "#0f3460",
    "assistant_bubble": "#16213e",
    "input_bg": "#0f3460",
    "border": "#2a2a4a",
}

FONTS = {
    "main": "'JetBrains Mono', 'Fira Code', 'Consolas', monospace",
}


# ====================
# API CLIENT FUNCTION
# ====================
async def ask_question_api(question: str, thread_id: str) -> dict:
    """
    Send question to the multi-agent API via HTTP.

    The API backend must be running on http://localhost:8000
    Start it with: uvicorn example1_langgraph_swarm.api:app --reload --port 8000

    Args:
        question: User's question
        thread_id: Unique conversation session ID

    Returns:
        dict with agent_name, content, and thread_id

    Raises:
        httpx.HTTPError: If API request fails
    """
    api_url = "http://localhost:8000/chat"  # Backend API endpoint

    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.post(
            api_url,
            json={"question": question, "thread_id": thread_id},
        )
        response.raise_for_status()
        return response.json()


def create_error_message(error: Exception) -> str:
    """
    Create user-friendly error message based on exception type.

    Args:
        error: The exception that occurred

    Returns:
        User-friendly error message
    """
    if isinstance(error, httpx.TimeoutException):
        return "⏱️ Request timeout. The agent is taking too long to respond. Please try again."

    if isinstance(error, httpx.HTTPStatusError):
        if error.response.status_code == 503:
            return "🔌 Service unavailable. Please make sure the API is running."
        if error.response.status_code == 422:
            return "⚠️ Invalid request format. Please try again with a different question."
        return f"❌ API error ({error.response.status_code}): {error.response.text}"

    if isinstance(error, httpx.ConnectError):
        return (
            "🔌 Cannot connect to API. The multi-agent system may be "
            "starting up. Please wait a moment and try again."
        )

    return f"❌ Unexpected error: {error!s}"


# ==========
# COMPONENTS
# ==========
@component
def chat_message(role: str, content: str, agent: str | None = None):
    """Render a single message of the chat with agent badge if applicable."""
    is_user = role == "user"

    container_style = {
        "display": "flex",
        "justifyContent": "flex-end" if is_user else "flex-start",
        "marginBottom": "16px",
        "padding": "0 20px",
    }

    bubble_style = {
        "maxWidth": "70%",
        "padding": "14px 18px",
        "borderRadius": "18px",
        "backgroundColor": (
            COLORS["user_bubble"] if is_user else COLORS["assistant_bubble"]
        ),
        "color": COLORS["text"],
        "fontFamily": FONTS["main"],
        "fontSize": "14px",
        "lineHeight": "1.6",
        "boxShadow": "0 2px 8px rgba(0, 0, 0, 0.3)",
        "border": f"1px solid {COLORS['border']}",
        "borderBottomRightRadius": "4px" if is_user else "18px",
        "borderBottomLeftRadius": "18px" if is_user else "4px",
        "whiteSpace": "pre-wrap",
        "wordBreak": "break-word",
    }

    role_label_style = {
        "fontSize": "11px",
        "color": COLORS["primary"] if is_user else COLORS["text_muted"],
        "marginBottom": "6px",
        "fontWeight": "600",
        "textTransform": "uppercase",
        "letterSpacing": "0.5px",
        "display": "flex",
        "alignItems": "center",
        "gap": "8px",
    }

    badge_style = {
        "display": "inline-flex",
        "alignItems": "center",
        "gap": "4px",
        "padding": "2px 8px",
        "borderRadius": "12px",
        "fontSize": "10px",
        "fontWeight": "500",
        "backgroundColor": "#2a5298" if agent == "CurriculumVitaeAgent" else "#2d7a3e",
        "color": "#ffffff",
    }

    # Determine role text and agent icon
    if is_user:
        role_text = "You"
        agent_badge = None
    else:
        role_text = "Assistant"
        if agent == "CurriculumVitaeAgent":
            agent_badge = html.span({"style": badge_style}, "📄 CV Agent")
        elif agent == "SearchAgent":
            agent_badge = html.span({"style": badge_style}, "🔍 Search Agent")
        else:
            agent_badge = None

    return html.div(
        {"style": container_style},
        html.div(
            {"style": bubble_style},
            html.div(
                {"style": role_label_style},
                role_text,
                agent_badge if agent_badge else None,
            ),
            html.div(content),
        ),
    )


@component
def loading_indicator():
    """Animated loading indicator."""
    container_style = {
        "display": "flex",
        "justifyContent": "flex-start",
        "marginBottom": "16px",
        "padding": "0 20px",
    }

    bubble_style = {
        "padding": "14px 18px",
        "borderRadius": "18px",
        "backgroundColor": COLORS["assistant_bubble"],
        "color": COLORS["text_muted"],
        "fontFamily": FONTS["main"],
        "fontSize": "14px",
        "border": f"1px solid {COLORS['border']}",
        "borderBottomLeftRadius": "4px",
    }

    return html.div(
        {"style": container_style},
        html.div(
            {"style": bubble_style},
            html.div(
                {
                    "style": {
                        "fontSize": "11px",
                        "color": COLORS["text_muted"],
                        "marginBottom": "6px",
                        "fontWeight": "600",
                        "textTransform": "uppercase",
                    }
                },
                "Assistant",
            ),
            html.div("Processing your question..."),
        ),
    )


@component
def chat_input(on_send, is_loading: bool):
    """Input field to send messages."""
    input_value, set_input_value = hooks.use_state("")

    container_style = {
        "display": "flex",
        "gap": "12px",
        "padding": "20px",
        "backgroundColor": COLORS["card"],
        "borderTop": f"1px solid {COLORS['border']}",
    }

    input_style = {
        "flex": "1",
        "padding": "14px 18px",
        "borderRadius": "12px",
        "border": f"2px solid {COLORS['border']}",
        "backgroundColor": COLORS["input_bg"],
        "color": COLORS["text"],
        "fontFamily": FONTS["main"],
        "fontSize": "14px",
        "outline": "none",
        "transition": "border-color 0.2s ease",
    }

    button_style = {
        "padding": "14px 28px",
        "borderRadius": "12px",
        "border": "none",
        "backgroundColor": COLORS["primary"] if not is_loading else COLORS["accent"],
        "color": COLORS["text"],
        "fontFamily": FONTS["main"],
        "fontSize": "14px",
        "fontWeight": "600",
        "cursor": "pointer" if not is_loading else "not-allowed",
        "transition": "all 0.2s ease",
        "opacity": "1" if not is_loading else "0.6",
    }

    def handle_input_change(event):
        set_input_value(event["target"]["value"])

    def handle_submit(event):
        if input_value.strip() and not is_loading:
            on_send(input_value.strip())
            set_input_value("")

    def handle_key_press(event):
        if event.get("key") == "Enter" and not event.get("shiftKey"):
            handle_submit(event)

    return html.div(
        {"style": container_style},
        html.input(
            {
                "type": "text",
                "value": input_value,
                "onChange": handle_input_change,
                "onKeyPress": handle_key_press,
                "placeholder": "Ask about the curriculum or search the web...",
                "style": input_style,
                "disabled": is_loading,
            }
        ),
        html.button(
            {
                "onClick": handle_submit,
                "style": button_style,
                "disabled": is_loading,
            },
            "Enviar" if not is_loading else "...",
        ),
    )


@component
def header_ui():
    """Application header."""
    header_style = {
        "padding": "24px 20px",
        "backgroundColor": COLORS["card"],
        "borderBottom": f"1px solid {COLORS['border']}",
        "textAlign": "center",
    }

    title_style = {
        "margin": "0",
        "color": COLORS["text"],
        "fontFamily": FONTS["main"],
        "fontSize": "24px",
        "fontWeight": "700",
        "letterSpacing": "-0.5px",
    }

    # subtitle_style = {
    #    "margin": "8px 0 0 0",
    #    "color": COLORS["text_muted"],
    #    "fontFamily": FONTS["main"],
    #    "fontSize": "13px",
    # }

    accent_style = {
        "color": COLORS["primary"],
    }

    subtitle_style = {
        "margin": "8px 0 0 0",
        "color": COLORS["text_muted"],
        "fontFamily": FONTS["main"],
        "fontSize": "13px",
    }

    return html.header(
        {"style": header_style},
        html.h1(
            {"style": title_style},
            html.span({"style": accent_style}, "Multi-Agent "),
            "Resume Analysis System",
        ),
        html.p(
            {"style": subtitle_style},
            "🤖 Powered by LangGraph Swarm • 📄 CV Agent • 🔍 Search Agent",
        ),
    )


@component
def footer_ui():
    """Application footer with developer information."""
    footer_style = {
        "padding": "20px",
        "backgroundColor": COLORS["card"],
        "borderTop": f"1px solid {COLORS['border']}",
        "textAlign": "center",
    }

    text_style = {
        "margin": "0 0 8px 0",
        "color": COLORS["text_muted"],
        "fontFamily": FONTS["main"],
        "fontSize": "13px",
        "lineHeight": "1.6",
    }

    link_style = {
        "color": COLORS["primary"],
        "textDecoration": "none",
        "fontWeight": "500",
        "transition": "color 0.2s ease",
    }

    return html.footer(
        {"style": footer_style},
        html.p(
            {"style": text_style},
            "Developed with ❤️",
        ),
        html.p(
            {"style": text_style},
            "LinkedIn: ",
            html.a(
                {
                    "href": "https://www.linkedin.com/in/eddy-giusepe-chirinos-isidro-phd-85a43a42/",
                    "target": "_blank",
                    "rel": "noopener noreferrer",
                    "style": link_style,
                },
                "Senior Data Scientist: Dr. Eddy Giusepe Chirinos Isidro",
            ),
        ),
    )


@component
def welcome_message():
    """Welcome message when there are no messages."""
    container_style = {
        "display": "flex",
        "flexDirection": "column",
        "alignItems": "center",
        "justifyContent": "center",
        "height": "100%",
        "padding": "40px",
        "textAlign": "center",
    }

    icon_style = {
        "fontSize": "64px",
        "marginBottom": "20px",
    }

    title_style = {
        "color": COLORS["text"],
        "fontFamily": FONTS["main"],
        "fontSize": "20px",
        "fontWeight": "600",
        "margin": "0 0 12px 0",
    }

    text_style = {
        "color": COLORS["text_muted"],
        "fontFamily": FONTS["main"],
        "fontSize": "14px",
        "lineHeight": "1.6",
        "maxWidth": "500px",
        "marginBottom": "12px",
    }

    agents_info_style = {
        "display": "flex",
        "gap": "12px",
        "marginTop": "16px",
        "marginBottom": "24px",
    }

    agent_card_style_base = {
        "padding": "12px 16px",
        "borderRadius": "12px",
        "border": f"1px solid {COLORS['border']}",
        "fontSize": "12px",
        "fontFamily": FONTS["main"],
        "display": "flex",
        "flexDirection": "column",
        "gap": "4px",
        "minWidth": "200px",
    }

    agent_card_cv = {**agent_card_style_base, "backgroundColor": "#1a2b4a"}
    agent_card_search = {**agent_card_style_base, "backgroundColor": "#1a3d2b"}

    agent_title_style = {
        "fontWeight": "600",
        "color": COLORS["text"],
        "fontSize": "13px",
    }

    agent_desc_style = {
        "color": COLORS["text_muted"],
        "fontSize": "11px",
        "lineHeight": "1.4",
    }

    suggestions_style = {
        "marginTop": "24px",
        "display": "flex",
        "flexDirection": "column",
        "gap": "8px",
    }

    suggestion_style = {
        "padding": "10px 16px",
        "backgroundColor": COLORS["accent"],
        "borderRadius": "8px",
        "color": COLORS["text_muted"],
        "fontFamily": FONTS["main"],
        "fontSize": "13px",
        "border": f"1px solid {COLORS['border']}",
    }

    return html.div(
        {"style": container_style},
        html.div({"style": icon_style}, "🤖"),
        html.h2({"style": title_style}, "Multi-Agent Resume Analysis System"),
        html.p(
            {"style": text_style},
            "I have two specialized agents to help you:",
        ),
        html.div(
            {"style": agents_info_style},
            html.div(
                {"style": agent_card_cv},
                html.div({"style": agent_title_style}, "📄 CV Agent"),
                html.div(
                    {"style": agent_desc_style},
                    "Analyzes professional curriculum, skills, experience, and education",
                ),
            ),
            html.div(
                {"style": agent_card_search},
                html.div({"style": agent_title_style}, "🔍 Search Agent"),
                html.div(
                    {"style": agent_desc_style},
                    "Searches the web for current information, news, and technologies",
                ),
            ),
        ),
        html.p(
            {"style": text_style},
            "The system automatically routes your question to the appropriate agent!",
        ),
        html.div(
            {"style": suggestions_style},
            html.div(
                {"style": suggestion_style},
                "💡 Example: What are the technical skills of this professional?",
            ),
            html.div(
                {"style": suggestion_style},
                "💡 Example: What is the latest news about AI and LangGraph?",
            ),
            html.div(
                {"style": suggestion_style},
                "💡 Example: What is the academic background of this candidate?",
            ),
        ),
    )


@component
def chat_app():
    """Main component of the chat."""
    messages, set_messages = hooks.use_state([])
    is_loading, set_is_loading = hooks.use_state(False)
    pending_question, set_pending_question = hooks.use_state(None)

    # Generate unique thread_id for this session (persists across component lifecycle)
    thread_id, _ = hooks.use_state(lambda: f"session-{uuid.uuid4()}")

    @hooks.use_effect(dependencies=[pending_question])
    async def process_pending_question():
        """Process the pending question when it changes."""
        if pending_question is None:
            return

        try:
            # Call the multi-agent API
            result = await ask_question_api(pending_question, thread_id)

            # Extract response data
            agent_name = result.get("agent_name", "Unknown")
            content = result.get("content", "")

            # Add the assistant's response with agent information
            assistant_message = {
                "role": "assistant",
                "content": content,
                "agent": agent_name,
            }
            set_messages(lambda prev: [*prev, assistant_message])

        except Exception as e:
            # Use helper function to create error message
            error_msg = create_error_message(e)
            assistant_message = {
                "role": "assistant",
                "content": error_msg,
                "agent": None,
            }
            set_messages(lambda prev: [*prev, assistant_message])

        finally:
            set_is_loading(False)
            set_pending_question(None)

    def handle_send(message: str):
        """Handle the sending of a new message."""
        # Add the user's message:
        new_user_message = {"role": "user", "content": message}
        set_messages(lambda prev: [*prev, new_user_message])
        set_is_loading(True)
        set_pending_question(message)

    # Main container styles:
    app_style = {
        "display": "flex",
        "flexDirection": "column",
        "height": "100vh",
        "backgroundColor": COLORS["background"],
        "fontFamily": FONTS["main"],
    }

    messages_container_style = {
        "flex": "1",
        "overflowY": "auto",
        "padding": "20px 0",
        "scrollBehavior": "smooth",
    }

    # Global CSS styles for scrollbar and font:
    global_style = f"""
        @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600;700&display=swap');

        * {{
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }}

        body {{
            background-color: {COLORS['background']};
            margin: 0;
            padding: 0;
        }}

        ::-webkit-scrollbar {{
            width: 8px;
        }}

        ::-webkit-scrollbar-track {{
            background: {COLORS['card']};
        }}

        ::-webkit-scrollbar-thumb {{
            background: {COLORS['accent']};
            border-radius: 4px;
        }}

        ::-webkit-scrollbar-thumb:hover {{
            background: {COLORS['primary']};
        }}

        input:focus {{
            border-color: {COLORS['primary']} !important;
        }}

        button:hover:not(:disabled) {{
            background-color: {COLORS['primary_hover']} !important;
            transform: translateY(-1px);
        }}
    """

    # Render the messages:
    message_elements = []
    if messages:
        for idx, msg in enumerate(messages):
            message_elements.append(
                chat_message(
                    role=msg["role"],
                    content=msg["content"],
                    agent=msg.get("agent"),
                    key=str(idx),
                )
            )

    return html.div(
        {"style": app_style},
        html.style(global_style),
        header_ui(),
        html.div(
            {"style": messages_container_style},
            welcome_message() if not messages else message_elements,
            loading_indicator() if is_loading else None,
        ),
        chat_input(on_send=handle_send, is_loading=is_loading),
        footer_ui(),
    )


# ==============================
# FASTAPI APPLICATION (UI ONLY)
# ==============================
app = FastAPI(
    title="Multi-Agent UI",
    description="""
Frontend interface for the Multi-Agent Resume Analysis System.

This UI consumes the backend API running on http://localhost:8000

## Features:
- **💬 Chat Interface**: Interactive ReactPy UI
- **📄 CV Agent Badge**: Visual indicator for curriculum questions
- **🔍 Search Agent Badge**: Visual indicator for web searches
- **🔄 Persistent Memory**: Thread-based conversation history
- **🎨 Modern Dark Theme**: Clean, professional design

## Backend API:
Make sure the API is running on port 8000:
```bash
uvicorn example1_langgraph_swarm.api:app --reload --port 8000
```
    """,
    version="1.0.0",
)

# Configure ReactPy UI
configure(app, chat_app)


if __name__ == "__main__":
    print("=" * 70)
    print("🎨 Multi-Agent UI - Frontend")
    print("=" * 70)
    print("💬 Interactive chat interface for multi-agent system")
    print("📄 CV Agent badge for curriculum questions")
    print("🔍 Search Agent badge for web searches")
    print("=" * 70)
    print("⚠️  IMPORTANT: Backend API must be running!")
    print("   Start API with:")
    print("   uvicorn example1_langgraph_swarm.api:app --reload --port 8000")
    print("=" * 70)
    print("🎨 UI Access: http://localhost:8080")
    print("🔌 API Backend: http://localhost:8000 (must be running)")
    print("📚 API Docs: http://localhost:8000/docs")
    print("=" * 70)
    print("🛑 Press Ctrl+C to stop\n")

    # Run UI on port 8080
    uvicorn.run(
        "ui:app",
        host="0.0.0.0",
        port=8080,
        reload=True,
        log_level="info",
    )
