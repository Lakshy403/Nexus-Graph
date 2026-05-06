# Nexus-Graph AI

> **AI-Powered Organizational Memory System** — Full-Stack Intelligence Platform

Nexus-Graph AI is an enterprise-grade platform that tracks decisions, discussions, and technical drift across workplace tools (Slack, GitHub, Jira). It builds a living, queryable knowledge graph and semantic memory, enabling teams to maintain alignment, detect policy violations in real-time, and reconstruct the causal lineage of organizational intelligence.

---

## Architecture Overview

```
┌─────────────┐     ┌──────────────┐     ┌──────────────────────────┐
│  Mock Slack  │────▶│              │     │   Python FastAPI Service  │
│  Mock GitHub │────▶│  Node.js     │────▶│                          │
│  Mock Jira   │────▶│  Gateway     │     │  ┌────────────────────┐  │
└─────────────┘     │              │     │  │  LangGraph Pipeline │  │
                    │  Express.js  │     │  │  ┌──────────────┐   │  │
                    │  Socket.io   │     │  │  │ 1. Parse      │   │  │
                    │              │     │  │  │ 2. Context    │   │  │
                    │  Redis ──────┼────▶│  │  │ 3. Extract    │   │  │
                    │  Pub/Sub     │     │  │  │ 4. Validate   │   │  │
                    │              │     │  │  │ 5. Store      │   │  │
                    │  MongoDB ◀───┼─────│  │  └──────────────┘   │  │
                    └──────────────┘     │  └────────────────────┘  │
                                        │                          │
                                        │  MongoDB ◀───────────────│
                                        │  Neo4j   ◀───────────────│
                                        │  ChromaDB ◀──────────────│
                                        └──────────────────────────┘
```

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Gateway | Node.js, Express.js, Socket.io, ioredis |
| AI Service | Python, FastAPI, LangGraph, Gemini API |
| Event Bus | Redis Pub/Sub |
| Document Store | MongoDB |
| Knowledge Graph | Neo4j |
| Semantic Memory | ChromaDB |
| Containers | Docker + Docker Compose |

## Project Structure

```
nexus-graph/
├── gateway/                    # Node.js event gateway
│   ├── Dockerfile
│   ├── package.json
│   └── src/
│       ├── index.js            # Express + Socket.io bootstrap
│       ├── config/
│       │   ├── index.js        # Configuration
│       │   ├── redis.js        # Redis publisher/subscriber
│       │   └── mongodb.js      # MongoDB client
│       ├── middleware/
│       │   ├── logger.js       # Request logger
│       │   └── validator.js    # Event validation
│       ├── routes/
│       │   ├── events.js       # POST /events/slack|github|jira
│       │   └── health.js       # GET /health
│       ├── services/
│       │   ├── eventBus.js     # Redis Pub/Sub publishing
│       │   └── socketManager.js# WebSocket management
│       └── utils/
│           └── logger.js       # Structured terminal logger
│
├── ai-service/                 # Python AI extraction service
│   ├── Dockerfile
│   ├── requirements.txt
│   └── src/
│       ├── main.py             # FastAPI app + lifecycle
│       ├── config/
│       │   └── settings.py     # Pydantic settings
│       ├── models/
│       │   └── schemas.py      # Data models
│       ├── db/
│       │   ├── mongodb.py      # Async MongoDB (Motor)
│       │   ├── neo4j_client.py # Neo4j graph operations
│       │   └── chromadb_client.py # Semantic embeddings
│       ├── services/
│       │   ├── decision_extractor.py  # Gemini LLM extraction
│       │   ├── conflict_detector.py   # Rule-based conflicts
│       │   ├── graph_builder.py       # Graph node builder
│       │   └── redis_subscriber.py    # Redis Pub/Sub consumer
│       ├── pipeline/
│       │   └── __init__.py     # LangGraph 5-node pipeline
│       └── utils/
│           └── logger.py       # Coloured structured logger
│
├── shared/
│   ├── mock_payloads/          # Sample event data
│   │   ├── slack_events.json
│   │   ├── github_events.json
│   │   └── jira_events.json
│   └── schemas/
│       └── event_schema.json   # JSON Schema
│
├── docker/
│   ├── mongo/init.js           # MongoDB initialization
│   └── neo4j/init.cypher       # Neo4j constraints & seeds
│
├── docker-compose.yml          # Full stack orchestration
├── .env.example                # Environment template
└── .gitignore
```

## Quick Start

### Prerequisites

- Docker & Docker Compose
- (Optional) Gemini API key for LLM extraction

### 1. Clone & Configure

```bash
cd nexus-graph
cp .env.example .env
# Edit .env and add your GEMINI_API_KEY (optional — keyword fallback works without it)
```

### 2. Start All Services

```bash
docker-compose up --build
```

This starts:
- **Redis** on port 6379
- **MongoDB** on port 27017
- **Neo4j** on ports 7474 (browser) / 7687 (bolt)
- **ChromaDB** on port 8000
- **Gateway** on port 3000
- **AI Service** on port 8001

### 3. Send Test Events

```bash
# Slack event — contains a decision
curl -X POST http://localhost:3000/events/slack \
  -H "Content-Type: application/json" \
  -d '{
    "type": "slack_message",
    "payload": {
      "user": "Backend Lead",
      "message": "Keep server cooling at 180°C max. This is a hard constraint.",
      "channel": "#infrastructure"
    }
  }'

# GitHub commit — will trigger conflict with the above decision
curl -X POST http://localhost:3000/events/github \
  -H "Content-Type: application/json" \
  -d '{
    "type": "github_commit",
    "payload": {
      "user": "dev-alice",
      "repo": "nexus-infra",
      "branch": "feature/cooling-update",
      "commit_sha": "a1b2c3d4e5f6",
      "message": "Update TEMP_LIMIT to 200 in cooling config",
      "diff": "- TEMP_LIMIT = 180\n+ TEMP_LIMIT = 200"
    }
  }'

# Jira ticket
curl -X POST http://localhost:3000/events/jira \
  -H "Content-Type: application/json" \
  -d '{
    "type": "jira_ticket",
    "payload": {
      "user": "Project Manager",
      "ticket_id": "NEXUS-101",
      "title": "Migrate auth service to OAuth2",
      "description": "Complete migration from basic auth to OAuth2. Target: End of Q2.",
      "status": "In Progress",
      "priority": "High"
    }
  }'
```

### 4. Query the AI Service

```bash
# Health check
curl http://localhost:8001/health

# View all extracted decisions
curl http://localhost:8001/decisions

# Semantic search
curl -X POST http://localhost:8001/search \
  -H "Content-Type: application/json" \
  -d '{"query": "temperature limits", "n_results": 5}'

# Full stats
curl http://localhost:8001/stats

# Direct event processing (bypass gateway)
curl -X POST http://localhost:8001/process \
  -H "Content-Type: application/json" \
  -d '{
    "type": "slack_message",
    "source": "slack",
    "payload": {
      "user": "CTO",
      "message": "All new services must use gRPC. REST is deprecated for inter-service communication."
    }
  }'
```

### 5. Explore Neo4j

Open http://localhost:7474 in your browser.

```cypher
// View all decisions and who made them
MATCH (p:Person)-[:MADE_DECISION]->(d:Decision)
RETURN p, d

// View conflicts
MATCH (d:Decision)-[:CONFLICTS_WITH]->(cf:Conflict)
RETURN d, cf

// Full graph
MATCH (n) RETURN n LIMIT 50
```

## Event Flow

```
1. Client sends POST /events/slack to Gateway
2. Gateway validates, enriches (UUID, timestamp), persists to MongoDB
3. Gateway publishes to Redis "slack-events" channel
4. AI Service subscriber receives the event
5. LangGraph pipeline executes:
   ├── Node 1: Parse event — extract raw text
   ├── Node 2: Analyze context — identify type, user, metadata
   ├── Node 3: Extract decisions — Gemini LLM or keyword fallback
   ├── Node 4: Validate + detect conflicts — rule-based checks
   └── Node 5: Store — MongoDB, Neo4j graph, ChromaDB embeddings
6. If conflicts found → published to "conflict-events" channel
7. If decision extracted → published to "decision-events" channel
8. Socket.io broadcasts to connected clients in real-time
```

## Conflict Detection Rules

| Rule | Example |
|------|---------|
| **Numeric Threshold** | Decision says max=180°C, commit sets TEMP_LIMIT=200 |
| **Deprecated Tech** | Decision says use OAuth2, commit adds basic-auth |
| **Policy Violation** | Decision mandates rate limiting, commit removes it |
| **Semantic Drift** | ChromaDB finds similar content with different values |

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `REDIS_URL` | `redis://redis:6379` | Redis connection |
| `MONGODB_URI` | `mongodb://mongo:27017/nexus_graph` | MongoDB connection |
| `NEO4J_URI` | `bolt://neo4j:7687` | Neo4j Bolt endpoint |
| `NEO4J_USER` | `neo4j` | Neo4j username |
| `NEO4J_PASSWORD` | `nexus_graph_2026` | Neo4j password |
| `CHROMA_HOST` | `chromadb` | ChromaDB hostname |
| `CHROMA_PORT` | `8000` | ChromaDB port |
| `GEMINI_API_KEY` | _(empty)_ | Google Gemini API key |
| `GATEWAY_PORT` | `3000` | Gateway HTTP port |
| `AI_SERVICE_PORT` | `8001` | AI Service HTTP port |

## Useful Commands

```bash
# Start everything
docker-compose up --build

# Start in background
docker-compose up -d --build

# View logs
docker-compose logs -f gateway
docker-compose logs -f ai-service

# Stop and remove volumes
docker-compose down -v

# Rebuild a single service
docker-compose up --build gateway
```

## Phase 2 Additions

Phase 2 adds the intelligence orchestration layer:

- gRPC contract in `shared/proto/nexus.proto`
- Gateway gRPC client with retry handling
- Python AI gRPC server on port `50051`
- LangGraph Phase 2 workflow with context retrieval, branching, validation, and storage
- ChromaDB memory for decisions and raw workplace events
- Advanced decision drift detection with severity, confidence, reasoning, and recommendations
- Mock Jira issue generation stored in `generated_issues`
- Timeline reconstruction stored in MongoDB and Neo4j
- Expanded Neo4j schema for `Incident`, `Recommendation`, `ArchitectureConstraint`, and `TimelineEvent`
- Socket.io events: `decision:created`, `conflict:detected`, `graph:update`, `timeline:update`, `orchestration:status`

More detail: `docs/phase2.md`.

## Phase 3 Frontend

The Phase 3 interface lives in `frontend/` and runs on port `3001`.

```bash
cd frontend
npm install
npm run dev
```

Routes:

- `/` cognitive operations dashboard
- `/graph` interactive React Flow knowledge graph
- `/timeline` temporal replay interface
- `/conflicts` decision drift monitor
- `/decisions` decision lineage explorer

---

---

**Phase 1** — Backend Architecture & Intelligence Foundation  
**Phase 2** — Orchestration & Real-Time Context Engine  
**Phase 3** — Cognitive Dashboard & Graph Visualization 

**Status** —  **Production-Ready Prototype Complete**
