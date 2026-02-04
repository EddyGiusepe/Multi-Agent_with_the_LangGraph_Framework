<font color="red"><h1 align="center">Quickstart - Multi-Agent System with langgraph swarm</h1></font>

<font color="pink">Senior Data Scientist.: Dr. Eddy Giusepe Chirinos Isidro</font>

This is a multi-agent system with LangGraph Swarm, RAG (CrewAI) and web search (Tavily).

## <font color="gree">Prerequisites</font>

1. **PostgreSQL** running (for state persistence):
   ```bash
   docker compose up -d
   ```

2. **Environment variables** in `.env`:
   ```env
   # Azure OpenAI
   AZURE_OPENAI_API_KEY=...
   AZURE_OPENAI_ENDPOINT=...
   AZURE_OPENAI_API_VERSION=...
   AZURE_OPENAI_DEPLOYMENT=...
   
   # Tavily (busca web)
   TAVILY_API_KEY=...
   
   # PostgreSQL
   POSTGRES_URI=postgresql://user:pass@localhost:5432/langgraph
   ```

3. **PDF of the curriculum** in `example1_langgraph_swarm/data/Data_Science_Eddy_en.pdf`

## <font color="gree">``Option 1:`` CLI (Interactive Terminal)</font>

```bash
# New modular CLI:
uv run cli.py

# OR original script (legacy):
uv run multi_agent_langgraph_swarm_and_crewai.py
```

## <font color="gree">``Option 2:`` API (FastAPI)</font>

### <font color="blue">Start server</font>

```bash
# Development (with hot reload):
uv run uvicorn api:app --reload --port 8000

# Production:
uv run uvicorn api:app --host 0.0.0.0 --port 8000
```

### <font color="blue">Endpoints</font>

| Method | Endpoint | Description |
|--------|----------|-----------|
| POST | `/chat` | Process question |
| GET | `/health` | Health check |
| GET | `/docs` | Swagger UI |

### <font color="blue">Example usage</font>

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What programming languages does the candidate know?",
    "thread_id": "user-session-123"
  }'
```

**Response:**
```json
{
  "agent_name": "CurriculumVitaeAgent",
  "content": "The candidate has experience with Python, JavaScript, SQL...",
  "thread_id": "user-session-123"
}
```

## <font color="gree">Structure of Modules</font>

```
example1_langgraph_swarm/
├── __init__.py     
├── database.py     # Context manager PostgreSQL
├── agents.py       # Agents and workflow
├── service.py      # Business logic (process_question)
├── api.py          # FastAPI endpoints
├── cli.py          # CLI modular
└── multi_agent_langgraph_swarm_and_crewai.py  # Legacy
```

## <font color="gree">Agents</font>

| Agent | Responsibility |
|--------|------------------|
| **CurriculumVitaeAgent** | Analyzes professional curriculum (RAG) |
| **SearchAgent** | Searches for information on the web (Tavily) |

The agents make **automatic handoff** between them according to the type of question.
