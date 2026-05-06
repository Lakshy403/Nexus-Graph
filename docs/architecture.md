# Nexus-Graph AI — Architecture Document

## System Design

### Event-Driven Architecture

Nexus-Graph uses an event-driven architecture where workplace events flow through
a central event bus (Redis Pub/Sub) and are processed asynchronously by the AI service.

### Data Flow

```
Workplace Tools → Gateway → Redis Pub/Sub → AI Service → Storage Layer
                    │                            │
                    ▼                            ├──▶ MongoDB (documents)
                 MongoDB                         ├──▶ Neo4j (graph)
               (raw events)                      └──▶ ChromaDB (embeddings)
```

### Knowledge Graph Schema

```
Node Types:
  - Person    {name, role, created_at}
  - Decision  {decision_id, text, constraint, category, importance}
  - Task      {task_id, title, status}
  - Commit    {sha, message, repo, branch}
  - Conflict  {conflict_id, type, severity, message}

Relationships:
  (Person)-[:MADE_DECISION]->(Decision)
  (Person)-[:AUTHORED]->(Commit)
  (Decision)-[:LINKED_TO]->(Task)
  (Task)-[:IMPLEMENTED_BY]->(Commit)
  (Decision)-[:CONFLICTS_WITH]->(Conflict)
```

### LangGraph Pipeline

The extraction pipeline has 5 sequential nodes:

1. **Parse Event** — Extracts raw text from the event payload
2. **Analyze Context** — Determines event type, user, metadata
3. **Extract Decisions** — Uses Gemini LLM (or keyword fallback) to identify decisions
4. **Validate & Detect** — Checks confidence threshold + runs conflict detection
5. **Store Results** — Writes to MongoDB, Neo4j, and ChromaDB

### Conflict Detection

Three rule-based strategies:

1. **Numeric Threshold** — Detects when new values exceed constrained limits
2. **Deprecated Technology** — Flags usage of technologies marked as deprecated
3. **Policy Violation** — Identifies removal of mandated features

Plus one semantic strategy:
4. **Semantic Drift** — Uses ChromaDB cosine similarity to find contradictions
