# ============================================
# Nexus-Graph AI Service - FastAPI + gRPC App
# ============================================

from __future__ import annotations

import time
from contextlib import asynccontextmanager
from typing import Any
from uuid import uuid4

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from src.config import get_settings
from src.utils.logger import get_logger
from src.db.mongodb import MongoDBClient
from src.db.neo4j_client import Neo4jClient
from src.db.chromadb_client import ChromaDBClient
from src.services.decision_extractor import DecisionExtractor
from src.services.conflict_detector import ConflictDetector
from src.services.graph_builder import GraphBuilder
from src.services.redis_subscriber import RedisSubscriber
from src.pipeline import ExtractionPipeline
from src.memory.retrieval import MemoryRetrievalService
from src.conflict_detection.engine import AdvancedConflictEngine
from src.langgraph.intelligence_workflow import IntelligenceWorkflow
from src.grpc_server.server import GrpcServerHandle, start_grpc_server

logger = get_logger("nexus-ai.main")

mongodb = MongoDBClient()
neo4j = Neo4jClient()
chromadb_client = ChromaDBClient()
extractor = DecisionExtractor()
redis_sub = RedisSubscriber()

conflict_detector: ConflictDetector | None = None
graph_builder: GraphBuilder | None = None
pipeline: ExtractionPipeline | None = None
workflow: IntelligenceWorkflow | None = None
grpc_handle: GrpcServerHandle | None = None


async def handle_event(event: dict[str, Any]) -> dict[str, Any] | None:
    """Run the Phase 2 workflow and fan out real-time backend events."""
    if workflow is None:
        logger.error("Workflow not initialized, dropping event")
        return None

    settings = get_settings()
    result = await workflow.process_event(event)

    await redis_sub.publish(settings.channel_orchestration, {
        "type": "orchestration_status",
        "event_id": result.get("event_id"),
        "correlation_id": result.get("correlation_id"),
        "stage": "complete",
        "metrics": result.get("metrics", {}),
    })

    for conflict in result.get("conflicts", []):
        await redis_sub.publish(settings.channel_conflicts, conflict)

    if result.get("stored") and result.get("extraction", {}).get("has_decision"):
        await redis_sub.publish(settings.channel_decisions, result["extraction"])

    for update in result.get("graph_updates", []):
        await redis_sub.publish(settings.channel_graph_updates, {
            "type": "graph_update",
            "event_id": result.get("event_id"),
            "correlation_id": result.get("correlation_id"),
            "update": update,
        })

    for entry in result.get("timeline", []):
        await redis_sub.publish(settings.channel_timeline, entry)

    return result


@asynccontextmanager
async def lifespan(app: FastAPI):
    global conflict_detector, graph_builder, pipeline, workflow, grpc_handle

    logger.info("Starting Nexus-Graph AI Service...")
    start = time.time()

    await mongodb.connect()
    await neo4j.connect()
    await chromadb_client.connect()

    extractor.initialize()

    conflict_detector = ConflictDetector(neo4j, chromadb_client)
    graph_builder = GraphBuilder(neo4j, chromadb_client)
    pipeline = ExtractionPipeline(extractor, conflict_detector, graph_builder, mongodb)

    memory = MemoryRetrievalService(chromadb_client, neo4j)
    advanced_conflicts = AdvancedConflictEngine()
    workflow = IntelligenceWorkflow(extractor, memory, advanced_conflicts, graph_builder, neo4j, mongodb)

    await redis_sub.connect()
    redis_sub.set_handler(handle_event)
    await redis_sub.start_listening()
    grpc_handle = await start_grpc_server(handle_event)

    elapsed = time.time() - start
    logger.info(f"AI Service ready in {elapsed:.1f}s")

    yield

    logger.info("Shutting down AI Service...")
    if grpc_handle:
        await grpc_handle.stop()
    await redis_sub.disconnect()
    await chromadb_client.disconnect()
    await neo4j.disconnect()
    await mongodb.disconnect()
    logger.info("AI Service stopped")


app = FastAPI(
    title="Nexus-Graph AI Service",
    description="AI-native orchestration and memory engine for organizational intelligence",
    version="2.0.0",
    lifespan=lifespan,
)


class EventRequest(BaseModel):
    event_id: str = ""
    correlation_id: str = ""
    type: str
    source: str
    timestamp: str = ""
    payload: dict[str, Any] = {}


class SearchRequest(BaseModel):
    query: str
    n_results: int = 5


@app.get("/")
async def root():
    return {
        "service": "Nexus-Graph AI Service",
        "version": "2.0.0",
        "phase": 2,
        "endpoints": {
            "health": "GET /health",
            "stats": "GET /stats",
            "process": "POST /process",
            "decisions": "GET /decisions",
            "search": "POST /search",
            "timeline": "GET /timeline/{correlation_id}",
            "graph_stats": "GET /graph/stats",
            "causal_chain": "GET /graph/causal-chain/{correlation_id}",
        },
        "grpc": "NexusIntelligence on port 50051",
    }


@app.get("/health")
async def health_check():
    checks = {}
    healthy = True
    try:
        checks["mongodb"] = {"status": "healthy", "collections": await mongodb.get_stats()}
    except Exception as e:
        checks["mongodb"] = {"status": "unhealthy", "error": str(e)}
        healthy = False
    try:
        checks["neo4j"] = {"status": "healthy", "nodes": await neo4j.get_graph_stats()}
    except Exception as e:
        checks["neo4j"] = {"status": "unhealthy", "error": str(e)}
        healthy = False
    try:
        checks["chromadb"] = {"status": "healthy", "embeddings": await chromadb_client.get_collection_count()}
    except Exception as e:
        checks["chromadb"] = {"status": "unhealthy", "error": str(e)}
        healthy = False
    checks["grpc"] = {"status": "healthy" if grpc_handle else "starting"}
    return {"service": "nexus-ai-service", "status": "healthy" if healthy else "degraded", "checks": checks}


@app.get("/stats")
async def get_stats():
    return {
        "mongodb": await mongodb.get_stats(),
        "neo4j": await neo4j.get_graph_stats(),
        "chromadb": {"embeddings": await chromadb_client.get_collection_count()},
    }


@app.post("/process")
async def process_event(req: EventRequest):
    if not workflow:
        raise HTTPException(503, "Workflow not initialized")
    event = req.model_dump()
    event["event_id"] = event.get("event_id") or str(uuid4())
    event["correlation_id"] = event.get("correlation_id") or event["event_id"]
    if not event.get("timestamp"):
        from datetime import datetime, timezone
        event["timestamp"] = datetime.now(timezone.utc).isoformat()
    return await handle_event(event)


@app.get("/decisions")
async def list_decisions():
    decisions = await neo4j.get_all_decisions()
    return {"count": len(decisions), "decisions": decisions}


@app.post("/search")
async def semantic_search(req: SearchRequest):
    results = await chromadb_client.search_similar(req.query, req.n_results)
    return {"query": req.query, "results": results}


@app.get("/timeline/{correlation_id}")
async def get_timeline(correlation_id: str):
    return {"correlation_id": correlation_id, "timeline": await mongodb.get_timeline(correlation_id)}


@app.get("/graph/stats")
async def graph_statistics():
    return {"graph": await neo4j.get_graph_stats()}


@app.get("/graph/causal-chain/{correlation_id}")
async def causal_chain(correlation_id: str):
    return {"correlation_id": correlation_id, "chain": await neo4j.reconstruct_causal_chain(correlation_id)}


@app.get("/graph/shortest-path")
async def shortest_path(left: str, right: str):
    return {"left": left, "right": right, "paths": await neo4j.shortest_path_between(left, right)}
