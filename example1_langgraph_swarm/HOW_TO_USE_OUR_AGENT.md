<font color="red"><h1 align="center">LangGraph Swarm Multi-Agent Usage Guide</h1></font>

<font color="pink">Senior Data Scientist.: Dr. Eddy Giusepe Chirinos Isidro</font>

---
## <font color="gree">``1.`` General Overview</font>

A multi-agent system based on ``LangGraph Swarm`` that combines professional curriculum analysis via RAG and real-time web search. The system uses a ``Frontend/Backend`` separated architecture for scalability and maintainability.

**Available Agents:**
- ``📄 CurriculumVitaeAgent``: Analyzes professional curriculum using RAG (Retrieval-Augmented Generation)
- ``🔍 SearchAgent``: Performs real-time web searches via Tavily

**Main Technologies:**
- LangGraph Swarm (multi-agent orchestration)
- FastAPI (backend REST)
- ReactPy (frontend)
- PostgreSQL (persistent memory)
- ChromaDB (vector database)
- CrewAI RagTool (RAG)
- Azure OpenAI (LLM and embeddings)
- Tavily (web search)

---
## <font color="gree">``2.`` Architecture</font>
You can visualize the architecture using ``MERMAID`` in the browser.

```mermaid
graph TB
    subgraph frontend [Frontend - Port 8080]
        UI[ReactPy UI]
        HTTPClient[HTTP Client]
    end
    
    subgraph backend [Backend - Port 8000]
        API[FastAPI API]
        Service[Service Layer]
        Workflow[Multi-Agent Workflow]
        CVAgent[CV Agent]
        SearchAgent[Search Agent]
        RAGTool[RAG Tool]
        TavilyTool[Tavily Search]
    end
    
    subgraph databases [Databases]
        Postgres[(PostgreSQL<br/>Port 5432)]
        Chroma[(ChromaDB<br/>Local)]
    end
    
    UI --> HTTPClient
    HTTPClient -->|POST /chat| API
    API --> Service
    Service --> Workflow
    Workflow --> CVAgent
    Workflow --> SearchAgent
    CVAgent --> RAGTool
    SearchAgent --> TavilyTool
    RAGTool --> Chroma
    Workflow --> Postgres
    API -->|Response| HTTPClient
    HTTPClient --> UI

    style frontend fill:#2d3748,stroke:#4a5568,color:#fff
    style backend fill:#1a365d,stroke:#2c5282,color:#fff
    style databases fill:#22543d,stroke:#2f855a,color:#fff
```

**Communication:**
- Frontend makes HTTP REST requests to the Backend
- Backend processes via multi-agent and returns JSON
- Clear separation of responsibilities

---

## <font color="gree">``3.`` Databases</font>

### <font color="blue">``3.1`` PostgreSQL</font>

**Function:** Stores the ``checkpointer`` of LangGraph for persistent memory of conversations.

**Configuration:**
- Docker Container: `langgraph_postgres`
- Port: `5432`
- Database: `langgraph_checkpoints`
- User/Password: `postgres/postgres`
- Persistent Storage: `postgres_data`

**What it stores:**
- Complete conversation history (``thread_id``)
- Agent state between interactions
- Context of ``handoffs`` between agents

**Initialization:**
```bash
cd example1_langgraph_swarm
docker-compose up -d
```

### <font color="blue">``3.2`` ChromaDB (Vector Database)</font>

**Function:** Stores embeddings of the PDF of the curriculum for the ``RagTool`` of CrewAI.

**Configuration:**
- Provider: ChromaDB with local persistence
- Location: `~/.local/share/example1_langgraph_swarm`
- Collection Name: `rag_cv_professional_langgraph`
- Embedding Model: Azure OpenAI (`text-embedding-3-large`)

**Characteristics:**
- **Persistence**: Embeddings are created once and reused
- **Economy**: Do not recreate embeddings in subsequent executions
- **Verification**: System verifies if collection exists before recreating
- **PDF Source**: `data/Data_Science_Eddy_en.pdf`
- **RAG Configuration**: 7 chunks, threshold 0.50

**Check Collections:**
```bash
uv run example1_langgraph_swarm/view_collections.py
```

---

## <font color="gree">``4.`` Backend (API)</font>

**Framework:** FastAPI on port `8000`

**Endpoints:**

| Endpoint | Method | Description |
|----------|--------|-----------|
| `/chat` | POST | Process questions through the multi-agent |
| `/health` | GET | Health check of the system |

**Request Model (`/chat`):**
```json
{
  "question": "What are the technical skills?",
  "thread_id": "session-abc123"
}
```

**Response Model:**
```json
{
  "agent_name": "CurriculumVitaeAgent",
  "content": "The professional has experience with...",
  "thread_id": "session-abc123"
}
```

**Lifecycle Management:**
- Connects to PostgreSQL on initialization
- Compiles multi-agent workflow
- Closes connections on shutdown

**Access:**
- API: http://localhost:8000
- Swagger Documentation: http://localhost:8000/docs
- Health Check: http://localhost:8000/health

**Execute:**
```bash
uvicorn example1_langgraph_swarm.api:app --reload --port 8000
```

---

## <font color="gree">``5.`` Frontend (UI)</font>

**Framework:** ReactPy + FastAPI on port `8080`

**Main Components:**
- `chat_message()`: Displays messages with badges of the agents
- `welcome_message()`: Cards informative about the agents
- `chat_input()`: User input with validation
- `loading_indicator()`: Loading indicator
- `header_ui()`: Header of the system
- `footer_ui()`: Footer with information

**Visual Badges:**
- 📄 **CV Agent** (blue `#2a5298`): Questions about the curriculum
- 🔍 **Search Agent** (green `#2d7a3e`): Web searches

**HTTP Client:**
- Uses `httpx.AsyncClient` for asynchronous communication
- Timeout: 120 seconds (to process RAG + LLM)
- Endpoint: `POST http://localhost:8000/chat`

**Error Handling:**
- ⏱️ Timeout: "The agent is taking too long..."
- 🔌 Connection Error: "Cannot connect to API..."
- 🔴 HTTP 503: "Service unavailable..."
- ⚠️ HTTP 422: "Invalid request format..."

**Access:**
- UI: http://localhost:8080

**Execute:**
```bash
uv run example1_langgraph_swarm/ui_reactpy/ui.py
```

---

## <font color="gree">``6.`` Setup and Execution</font>

### <font color="blue">``6.1`` Prerequisites</font>

- Python 3.13+
- Docker and Docker Compose
- UV Package Manager
- Environment variables in `.env`:

```bash
# Azure OpenAI
AZURE_OPENAI_API_KEY=your_key
AZURE_OPENAI_ENDPOINT=your_endpoint
AZURE_OPENAI_DEPLOYMENT=your_deployment
AZURE_OPENAI_API_VERSION=2024... 
AZURE_OPENAI_EMBED_DEPLOYMENT_LARGE=text-embedding...

# Tavily Search
TAVILY_API_KEY=your_tavily_key

# PostgreSQL
POSTGRES_URI=postgresql+psycopg://postgres:postgres@localhost:5432/langgraph_checkpoints
```

### <font color="blue">``6.2`` Installation</font>

```bash
# Clone the repository
cd /path/to/project

# Install dependencies
uv sync
```

### <font color="blue">``6.3`` Execution (3 Steps)</font>

**Step 1: Start PostgreSQL**
```bash
cd example1_langgraph_swarm
docker-compose up -d

# Check
docker-compose ps
```

**Step 2: Start Backend (Terminal 1)**
```bash
uvicorn example1_langgraph_swarm.api:app --reload --port 8000
```

**Step 3: Start Frontend (Terminal 2)**
```bash
uv run example1_langgraph_swarm/ui_reactpy/ui.py
```

### <font color="blue">``6.4`` Accesses</font>

| Service | URL | Description |
|---------|-----|-----------|
| Frontend UI | http://localhost:8080 | User interface |
| Backend API | http://localhost:8000 | REST API |
| API Docs | http://localhost:8000/docs | Swagger/OpenAPI |
| Health Check | http://localhost:8000/health | System status |

### <font color="blue">``6.5`` Stop the System</font>

```bash
# Frontend (Terminal 2)
Ctrl+C

# Backend (Terminal 1)
Ctrl+C

# PostgreSQL
cd example1_langgraph_swarm
docker-compose down
```

---

## <font color="gree">``7.`` Data Flow</font>

```mermaid
sequenceDiagram
    participant User
    participant UI as Frontend UI<br/>(Port 8080)
    participant API as Backend API<br/>(Port 8000)
    participant Workflow as Multi-Agent<br/>Workflow
    participant Agent as CV/Search<br/>Agent
    participant DB as PostgreSQL<br/>(Checkpointer)
    participant Chroma as ChromaDB<br/>(Embeddings)

    User->>UI: Digite pergunta
    UI->>UI: Gera thread_id único
    UI->>API: POST /chat<br/>{question, thread_id}
    API->>Workflow: Processa pergunta
    Workflow->>Agent: Roteia para agente apropriado
    
    alt CV Agent
        Agent->>Chroma: Busca embeddings (RAG)
        Chroma-->>Agent: Chunks relevantes
    else Search Agent
        Agent->>Agent: Busca Tavily (web)
    end
    
    Agent->>Workflow: Resposta gerada
    Workflow->>DB: Salva contexto (thread_id)
    Workflow-->>API: {agent_name, content, thread_id}
    API-->>UI: JSON Response
    UI->>UI: Exibe badge + mensagem
    UI-->>User: Mostra resposta
```

**Detail:**

1. **User** types question in the UI (port 8080)
2. **UI** generates a unique `thread_id` (format: `session-<uuid>`)
3. **UI** sends `POST /chat` with `{question, thread_id}` to API (port 8000)
4. **Backend** routes to the appropriate agent:
   - Questions about the curriculum → **CurriculumVitaeAgent** → RAG (ChromaDB)
   - Questions about web/events → **SearchAgent** → Tavily
5. **Agent** processes and generates response via Azure OpenAI
6. **Workflow** saves context in **PostgreSQL** (checkpointer)
7. **Backend** returns JSON: `{agent_name, content, thread_id}`
8. **UI** displays response with badge color of the agent

---

## <font color="gree">``8.`` Examples of Usage</font>

### ``Example 1:`` Curriculum Analysis (CV Agent)

**Question:**
```
What are the technical skills of this professional?
```

**Expected Response:**
- Badge: 📄 CV Agent (blue)
- Content: Information extracted from PDF via RAG
- Source: ChromaDB embeddings

### ``Example 2:`` Web Search (Search Agent)

**Question:**
```
What is the latest news about LangGraph?
```

**Expected Response:**
- Badge: 🔍 Search Agent (verde)
- Content: Current information from the web
- Source: Tavily API

### ``Example 3``: Persistent Memory

**Conversation:**
```
User: What programming languages does the candidate know?
Agent: The candidate has experience with Python, R, SQL...

User: Does he have data science experience?
Agent: Yes, as mentioned before, the candidate has... [uses previous context]
```

**Behavior:**
- Same `thread_id` maintains context
- PostgreSQL stores history
- Agent references previous messages

### ``Example 4``: Automatic Handoff

**Question:**
```
Compare the candidate's AI expertise with the latest AI trends
```

**Behavior:**
- CV Agent: Extracts expertise from the curriculum
- Search Agent: Searches current trends
- Workflow: Combines information from both
- There may be multiple automatic handoffs

---

## <font color="gree">``9.`` Troubleshooting</font>

| Error | Cause | Solution |
|------|-------|---------|
| 🔌 "Cannot connect to API" | Backend is not running | Start backend: `uvicorn example1_langgraph_swarm.api:app --reload --port 8000` |
| 🔴 "Service not ready - workflow not initialized" | PostgreSQL is not connected | Check: `docker-compose ps` and restart if necessary |
| ⏱️ "Request timeout" | Processing takes too long (>120s) | Normal on first execution (creating embeddings). Wait. |
| ⚠️ "Collection already exists" | ChromaDB reutilizing embeddings | **Normal and expected!** System optimized to reuse embeddings. |
| UI loads but does not respond | Backend on different port or CORS error | Check backend logs and browser console (F12) |

**First Execution Takes Time:**
- ChromaDB creates embeddings of the PDF for the first time
- Can take a few minutes (Azure OpenAI embeddings)
- Subsequent executions are fast (reused embeddings)

**Check Logs:**
```bash
# Backend logs (Terminal 1)
# Look for: "Connection established", "Workflow compiled"

# Frontend logs (Terminal 2)
# Look for: "Starting server", "ReactPy configured"

# PostgreSQL logs
docker-compose logs postgres
```

**Test API Directly:**
```bash
# Health check
curl http://localhost:8000/health

# Send question
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"question": "What are the technical skills?", "thread_id": "test-123"}'
```

---

## <font color="gree">``10.`` File Structure</font>

```
example1_langgraph_swarm/
├── agents.py              # Definition of agents and workflow
├── api.py                 # Backend FastAPI
├── config_rag_azure.py    # Configuration RAG + ChromaDB
├── database.py            # PostgreSQL connection
├── service.py             # Service layer
├── docker-compose.yml     # PostgreSQL container
├── data/
│   └── Data_Science_Eddy_en.pdf  # Curriculum for RAG
└── ui_reactpy/
    └── ui.py              # Frontend ReactPy
```

**Databases:**
- PostgreSQL: Docker Container (port 5432)
- ChromaDB: `~/.local/share/example1_langgraph_swarm`

---

## <font color="gree">``11.`` Technical Specifications</font>

### RAG Tool (CrewAI)
- Library: `crewai_tools.RagTool`
- PDF: `data/Data_Science_Eddy_en.pdf`
- Chunks: 7 documents retrieved
- Similarity Threshold: 0.50
- Embedding Model: Azure OpenAI `text-embedding-3-large`
- Vector DB: ChromaDB (local persistence)
- Collection: `rag_cv_professional_langgraph`

### Multi-Agent Workflow
- Framework: LangGraph Swarm
- Checkpointer: AsyncPostgresSaver (PostgreSQL)
- Automatic Handoff: Yes (between CV and Search Agent)
- Memory: Persistent via thread_id

### Azure OpenAI Models
- LLM: Configured via `AZURE_OPENAI_DEPLOYMENT`
- Embeddings: `text-embedding-3-large`
- API Version: `2024-02-15-preview`

### Tavily Search
- API: Tavily Search
- Usage: Real-time web searches
- Configuration: `TAVILY_API_KEY` in `.env`

---

## <font color="gree">``12.`` System Metrics</font>

**Architecture:**
- Separation Frontend/Backend: ✅ Complete
- Independent ports: ✅ 8080 (UI) / 8000 (API)
- Scalability: ✅ Components can scale separately

**Performance:**
- First execution: ~60-120s (creating embeddings)
- Subsequent executions: ~5-10s (reusing embeddings)
- Maximum timeout: 120s

**Code:**
- Frontend (ui.py)
- Backend (api.py)
- Agents (agents.py)

---

## <font color="gree">``13.`` Conclusion</font>

The Multi-Agent LangGraph Swarm system offers:

✅ **Modern architecture**: Frontend/Backend separated  
✅ **Efficient databases**: PostgreSQL (memory) + ChromaDB (embeddings)  
✅ **Optimized RAG**: Reuse embeddings via CrewAI RagTool  
✅ **Intelligent multi-agent**: Automatic handoff between CV and Search  
✅ **Persistent memory**: Context maintained via thread_id  
✅ **Intuitive interface**: Visual badges identify agents  

**System ready for production with scalability and maintainability guaranteed!** 🚀
