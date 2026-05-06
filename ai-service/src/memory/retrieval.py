from __future__ import annotations

import time
from typing import Any

from src.db.chromadb_client import ChromaDBClient
from src.db.neo4j_client import Neo4jClient
from src.embeddings.text import event_text, summarize_event
from src.utils.logger import get_logger

logger = get_logger("nexus-ai.memory")


class MemoryRetrievalService:
    """Retrieves semantically and graph-related context for an incoming event."""

    def __init__(self, chromadb: ChromaDBClient, neo4j: Neo4jClient):
        self._chromadb = chromadb
        self._neo4j = neo4j

    async def store_event_memory(self, event: dict[str, Any], extraction: dict[str, Any] | None = None) -> None:
        text = event_text(event)
        if not text:
            return
        await self._chromadb.store_memory(
            memory_id=event.get("event_id", ""),
            text=summarize_event(event),
            kind=event.get("source", "event"),
            metadata={
                "event_id": event.get("event_id", ""),
                "correlation_id": event.get("correlation_id", event.get("event_id", "")),
                "source": event.get("source", ""),
                "type": event.get("type", ""),
                "has_decision": bool((extraction or {}).get("has_decision")),
            },
        )

    async def retrieve_context(self, event: dict[str, Any], limit: int = 6) -> dict[str, Any]:
        started = time.perf_counter()
        query = event_text(event)
        semantic = await self._chromadb.search_similar(query, n_results=limit) if query else []
        graph = await self._neo4j.find_related_context(query, limit=limit) if query else []

        ranked = []
        for item in semantic:
            ranked.append({
                "id": item.get("id", ""),
                "kind": item.get("metadata", {}).get("kind", "semantic_memory"),
                "summary": item.get("document", ""),
                "score": 1.0 - float(item.get("distance") or 1.0),
                "metadata": item.get("metadata", {}),
            })
        for item in graph:
            ranked.append({
                "id": item.get("id", ""),
                "kind": item.get("kind", "graph_context"),
                "summary": item.get("summary", ""),
                "score": float(item.get("score", 0.55)),
                "metadata": item,
            })

        ranked.sort(key=lambda x: x["score"], reverse=True)
        elapsed_ms = round((time.perf_counter() - started) * 1000, 2)
        logger.info("Context retrieved", extra={"meta": {"items": len(ranked[:limit]), "latency_ms": elapsed_ms}})
        return {"items": ranked[:limit], "latency_ms": elapsed_ms}
