# Nexus-Graph AI - Phase 2

## Intelligence, Orchestration & Real-Time Context Engine

Phase 2 adds a production-inspired intelligence layer on top of the Phase 1 event bus.

### Service Communication

- `shared/proto/nexus.proto` defines the `NexusIntelligence` gRPC contract.
- The gateway uses `@grpc/grpc-js` as a client.
- The AI service runs a Python gRPC server on port `50051`.
- Redis remains the event bus and real-time fanout path.
- gRPC is the primary gateway-to-AI processing path, with Redis fallback metadata.

### LangGraph Workflow

The Phase 2 workflow lives in `ai-service/src/langgraph/intelligence_workflow.py`.

Steps:

1. Classify event type and implementation/security signals
2. Retrieve semantic context from ChromaDB
3. Query Neo4j for graph-related decisions and constraints
4. Run decision extraction
5. Detect decision drift and conflicts
6. Generate recommendations and mock Jira issues
7. Store memory, graph relationships, issues, and timeline events
8. Publish orchestration-ready results

The graph includes a context retry branch and a conflict branch.

### Real-Time Event Types

Socket.io broadcasts named events for Phase 3 frontend integration:

- `decision:created`
- `conflict:detected`
- `graph:update`
- `timeline:update`
- `orchestration:status`

### Expanded Graph Schema

New nodes:

- `Incident`
- `Recommendation`
- `ArchitectureConstraint`
- `TimelineEvent`

New relationships:

- `CAUSED_BY`
- `VIOLATES`
- `RELATED_TO`
- `RECOMMENDED_FIX`
- `HISTORICALLY_LINKED`

### Timeline Reconstruction

Timeline events are stored in MongoDB and Neo4j with `correlation_id`, enabling flows like:

`Slack Discussion -> Architecture Decision -> Jira Task -> GitHub Commit -> Conflict -> Recommendation`

Useful endpoints:

- `GET /timeline/{correlation_id}`
- `GET /graph/causal-chain/{correlation_id}`
- `GET /graph/shortest-path?left={id}&right={id}`

### Phase 2 Test Sequence

Use `shared/mock_payloads/phase2_conflict_sequence.json` to seed:

1. OAuth token expiry decision
2. Linked Jira implementation task
3. GitHub commit that changes `TOKEN_EXPIRY_HOURS` from `24` to `72`

Expected result:

- conflict detection
- generated issue in MongoDB
- recommendation node in Neo4j
- timeline updates over Socket.io
