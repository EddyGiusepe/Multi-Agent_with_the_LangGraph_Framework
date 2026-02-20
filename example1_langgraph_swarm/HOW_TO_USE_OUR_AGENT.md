<font color="red"><h1 align="center">Guia de Uso do Multi-Agent LangGraph Swarm</h1></font>

<font color="pink">Senior Data Scientist.: Dr. Eddy Giusepe Chirinos Isidro</font>

---
## <font color="gree">``1.`` Visão Geral</font>

Sistema multi-agente baseado em **LangGraph Swarm** que combina análise de currículo via RAG e busca web em tempo real. O sistema utiliza arquitetura Frontend/Backend separados para escalabilidade e manutenibilidade.

**Agentes Disponíveis:**
- ``📄 CurriculumVitaeAgent``: Analisa currículo profissional usando RAG (Retrieval-Augmented Generation)
- ``🔍 SearchAgent``: Realiza buscas na web em tempo real via Tavily

**Tecnologias Principais:**
- LangGraph Swarm (orquestração multi-agente)
- FastAPI (backend REST)
- ReactPy (frontend)
- PostgreSQL (memória persistente)
- ChromaDB (banco vetorial)
- CrewAI RagTool (RAG)
- Azure OpenAI (LLM e embeddings)
- Tavily (web search)

---
## <font color="gree">``2.`` Arquitetura</font>
Você pode visualizar a arquitetura usando ``MERMAID`` no browser.

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

**Comunicação:**
- Frontend faz requisições HTTP REST para o Backend
- Backend processa via multi-agente e retorna JSON
- Separação clara de responsabilidades

---

## <font color="gree">``3.`` Bancos de Dados</font>

### <font color="blue">``3.1`` PostgreSQL</font>

**Função:** Armazena o **checkpointer** do LangGraph para memória persistente de conversas.

**Configuração:**
- Container Docker: `langgraph_postgres`
- Porta: `5432`
- Database: `langgraph_checkpoints`
- User/Password: `postgres/postgres`
- Volume persistente: `postgres_data`

**O que armazena:**
- Histórico completo de conversas (``thread_id``)
- Estado dos agentes entre interações
- Contexto de ``handoffs`` entre agentes

**Inicialização:**
```bash
cd example1_langgraph_swarm
docker-compose up -d
```

### <font color="blue">``3.2`` ChromaDB (Banco Vetorial)</font>

**Função:** Armazena embeddings do PDF do currículo para o **RagTool** da CrewAI.

**Configuração:**
- Provider: ChromaDB com persistência local
- Localização: `~/.local/share/example1_langgraph_swarm`
- Collection: `rag_cv_professional_langgraph`
- Embedding Model: Azure OpenAI (`text-embedding-3-large`)

**Características:**
- **Persistência**: Embeddings são criados uma única vez e reutilizados
- **Economia**: Não recria embeddings em execuções subsequentes
- **Verificação**: Sistema verifica se collection existe antes de recriar
- **PDF Source**: `data/Data_Science_Eddy_en.pdf`
- **Configuração RAG**: 7 chunks, threshold 0.50

**Verificar Collections:**
```bash
uv run example1_langgraph_swarm/view_collections.py
```

---

## <font color="gree">``4.`` Backend (API)</font>

**Framework:** FastAPI na porta `8000`

**Endpoints:**

| Endpoint | Método | Descrição |
|----------|--------|-----------|
| `/chat` | POST | Processa perguntas através do multi-agente |
| `/health` | GET | Health check do sistema |

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
- Conecta ao PostgreSQL na inicialização
- Compila workflow multi-agente
- Fecha conexões no shutdown

**Acessar:**
- API: http://localhost:8000
- Documentação Swagger: http://localhost:8000/docs
- Health Check: http://localhost:8000/health

**Executar:**
```bash
uvicorn example1_langgraph_swarm.api:app --reload --port 8000
```

---

## <font color="gree">``5.`` Frontend (UI)</font>

**Framework:** ReactPy + FastAPI na porta `8080`

**Componentes Principais:**
- `chat_message()`: Exibe mensagens com badges dos agentes
- `welcome_message()`: Cards informativos sobre os agentes
- `chat_input()`: Input do usuário com validação
- `loading_indicator()`: Indicador de processamento
- `header_ui()`: Cabeçalho do sistema
- `footer_ui()`: Rodapé com informações

**Badges Visuais:**
- 📄 **CV Agent** (azul `#2a5298`): Perguntas sobre currículo
- 🔍 **Search Agent** (verde `#2d7a3e`): Buscas na web

**Cliente HTTP:**
- Usa `httpx.AsyncClient` para comunicação assíncrona
- Timeout: 120 segundos (para processar RAG + LLM)
- Endpoint: `POST http://localhost:8000/chat`

**Tratamento de Erros:**
- ⏱️ Timeout: "The agent is taking too long..."
- 🔌 Connection Error: "Cannot connect to API..."
- 🔴 HTTP 503: "Service unavailable..."
- ⚠️ HTTP 422: "Invalid request format..."

**Acessar:**
- UI: http://localhost:8080

**Executar:**
```bash
uv run example1_langgraph_swarm/ui_reactpy/ui.py
```

---

## <font color="gree">``6.`` Setup e Execução</font>

### <font color="blue">``6.1`` Pré-requisitos</font>

- Python 3.13+
- Docker e Docker Compose
- UV package manager
- Variáveis de ambiente no `.env`:

```bash
# Azure OpenAI
AZURE_OPENAI_API_KEY=your_key
AZURE_OPENAI_ENDPOINT=your_endpoint
AZURE_OPENAI_DEPLOYMENT=your_deployment
AZURE_OPENAI_API_VERSION=2024 . . . 
AZURE_OPENAI_EMBED_DEPLOYMENT_LARGE=text-embedding . . .

# Tavily Search
TAVILY_API_KEY=your_tavily_key

# PostgreSQL
POSTGRES_URI=postgresql+psycopg://postgres:postgres@localhost:5432/langgraph_checkpoints
```

### <font color="blue">``6.2`` Instalação</font>

```bash
# Clonar repositório
cd /path/to/project

# Instalar dependências
uv sync
```

### <font color="blue">``6.3`` Execução (3 Passos)</font>

**Passo 1: Iniciar PostgreSQL**
```bash
cd example1_langgraph_swarm
docker-compose up -d

# Verificar
docker-compose ps
```

**Passo 2: Iniciar Backend (Terminal 1)**
```bash
uvicorn example1_langgraph_swarm.api:app --reload --port 8000
```

**Passo 3: Iniciar Frontend (Terminal 2)**
```bash
uv run example1_langgraph_swarm/ui_reactpy/ui.py
```

### <font color="blue">``6.4`` Acessos</font>

| Serviço | URL | Descrição |
|---------|-----|-----------|
| Frontend UI | http://localhost:8080 | Interface do usuário |
| Backend API | http://localhost:8000 | REST API |
| API Docs | http://localhost:8000/docs | Swagger/OpenAPI |
| Health Check | http://localhost:8000/health | Status do sistema |

### <font color="blue">``6.5`` Parar o Sistema</font>

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

## <font color="gree">``7.`` Fluxo de Dados</font>

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

**Detalhamento:**

1. **Usuário** digita pergunta na UI (porta 8080)
2. **UI** gera `thread_id` único (formato: `session-<uuid>`)
3. **UI** envia `POST /chat` com `{question, thread_id}` para API (porta 8000)
4. **Backend** roteia para agente apropriado:
   - Perguntas sobre currículo → **CurriculumVitaeAgent** → RAG (ChromaDB)
   - Perguntas sobre web/eventos → **SearchAgent** → Tavily
5. **Agente** processa e gera resposta via Azure OpenAI
6. **Workflow** salva contexto no **PostgreSQL** (checkpointer)
7. **Backend** retorna JSON: `{agent_name, content, thread_id}`
8. **UI** exibe resposta com badge colorido do agente

---

## <font color="gree">``8.`` Exemplos de Uso</font>

### ``Exemplo 1:`` Análise de Currículo (CV Agent)

**Pergunta:**
```
What are the technical skills of this professional?
```

**Resposta Esperada:**
- Badge: 📄 CV Agent (azul)
- Conteúdo: Informações extraídas do PDF via RAG
- Fonte: ChromaDB embeddings

### ``Exemplo 2:`` Busca Web (Search Agent)

**Pergunta:**
```
What is the latest news about LangGraph?
```

**Resposta Esperada:**
- Badge: 🔍 Search Agent (verde)
- Conteúdo: Informações atuais da web
- Fonte: Tavily API

### ``Exemplo 3``: Memória Persistente

**Conversa:**
```
User: What programming languages does the candidate know?
Agent: The candidate has experience with Python, R, SQL...

User: Does he have data science experience?
Agent: Yes, as mentioned before, the candidate has... [usa contexto anterior]
```

**Comportamento:**
- Mesmo `thread_id` mantém contexto
- PostgreSQL armazena histórico
- Agente referencia mensagens anteriores

### ``Exemplo 4``: Handoff Automático

**Pergunta:**
```
Compare the candidate's AI expertise with the latest AI trends
```

**Comportamento:**
- CV Agent: Extrai expertise do currículo
- Search Agent: Busca tendências atuais
- Workflow: Combina informações de ambos
- Pode haver múltiplos handoffs automáticos

---

## <font color="gree">``9.`` Troubleshooting</font>

| Erro | Causa | Solução |
|------|-------|---------|
| 🔌 "Cannot connect to API" | Backend não está rodando | Inicie backend: `uvicorn example1_langgraph_swarm.api:app --reload --port 8000` |
| 🔴 "Service not ready - workflow not initialized" | PostgreSQL não conectado | Verifique: `docker-compose ps` e reinicie se necessário |
| ⏱️ "Request timeout" | Processamento demorado (>120s) | Normal na primeira execução (criando embeddings). Aguarde. |
| ⚠️ "Collection already exists" | ChromaDB reutilizando embeddings | **Normal e esperado!** Sistema otimizado para reutilizar embeddings. |
| UI carrega mas não responde | Backend em porta diferente ou erro CORS | Verifique logs do backend e console do navegador (F12) |

**Primeira Execução Demora:**
- ChromaDB cria embeddings do PDF pela primeira vez
- Pode levar alguns minutos (Azure OpenAI embeddings)
- Execuções subsequentes são rápidas (embeddings reutilizados)

**Verificar Logs:**
```bash
# Backend logs (Terminal 1)
# Busque por: "Connection established", "Workflow compiled"

# Frontend logs (Terminal 2)
# Busque por: "Starting server", "ReactPy configured"

# PostgreSQL logs
docker-compose logs postgres
```

**Testar API Diretamente:**
```bash
# Health check
curl http://localhost:8000/health

# Enviar pergunta
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"question": "What are the technical skills?", "thread_id": "test-123"}'
```

---

## <font color="gree">``10.`` Estrutura de Arquivos</font>

```
example1_langgraph_swarm/
├── agents.py              # Definição dos agentes e workflow
├── api.py                 # Backend FastAPI
├── config_rag_azure.py    # Configuração RAG + ChromaDB
├── database.py            # Conexão PostgreSQL
├── service.py             # Camada de serviço
├── docker-compose.yml     # PostgreSQL container
├── data/
│   └── Data_Science_Eddy_en.pdf  # Currículo para RAG
└── ui_reactpy/
    └── ui.py              # Frontend ReactPy
```

**Bancos de Dados:**
- PostgreSQL: Container Docker (porta 5432)
- ChromaDB: `~/.local/share/example1_langgraph_swarm`

---

## <font color="gree">``11.`` Especificações Técnicas</font>

### RAG Tool (CrewAI)
- Biblioteca: `crewai_tools.RagTool`
- PDF: `data/Data_Science_Eddy_en.pdf`
- Chunks: 7 documentos recuperados
- Similarity Threshold: 0.50
- Embedding Model: Azure OpenAI `text-embedding-3-large`
- Vector DB: ChromaDB (persistência local)
- Collection: `rag_cv_professional_langgraph`

### Multi-Agent Workflow
- Framework: LangGraph Swarm
- Checkpointer: AsyncPostgresSaver (PostgreSQL)
- Handoff Automático: Sim (entre CV e Search Agent)
- Memória: Persistente via thread_id

### Modelos Azure OpenAI
- LLM: Configurado via `AZURE_OPENAI_DEPLOYMENT`
- Embeddings: `text-embedding-3-large`
- API Version: `2024-02-15-preview`

### Tavily Search
- API: Tavily Search
- Uso: Buscas web em tempo real
- Configuração: `TAVILY_API_KEY` no `.env`

---

## <font color="gree">``12.`` Métricas do Sistema</font>

**Arquitetura:**
- Separação Frontend/Backend: ✅ Completa
- Portas independentes: ✅ 8080 (UI) / 8000 (API)
- Escalabilidade: ✅ Componentes podem escalar separadamente

**Performance:**
- Primeira execução: ~60-120s (criação embeddings)
- Execuções subsequentes: ~5-10s (reutiliza embeddings)
- Timeout máximo: 120s

**Código:**
- Frontend (ui.py): ~420 linhas
- Backend (api.py): ~182 linhas
- Agentes (agents.py): ~280 linhas

---

## <font color="gree">``13.`` Conclusão</font>

O sistema Multi-Agent LangGraph Swarm oferece:

✅ **Arquitetura moderna**: Frontend/Backend separados  
✅ **Bancos de dados eficientes**: PostgreSQL (memória) + ChromaDB (embeddings)  
✅ **RAG otimizado**: Reutilização de embeddings via CrewAI RagTool  
✅ **Multi-agente inteligente**: Handoff automático entre CV e Search  
✅ **Memória persistente**: Contexto mantido via thread_id  
✅ **Interface intuitiva**: Badges visuais identificam agentes  

**Sistema pronto para uso em produção com escalabilidade e manutenibilidade garantidas!** 🚀
