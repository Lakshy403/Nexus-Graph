from __future__ import annotations

import time
from typing import Any, TypedDict
from uuid import uuid4

from langgraph.graph import END, StateGraph

from src.conflict_detection.engine import AdvancedConflictEngine
from src.db.mongodb import MongoDBClient
from src.db.neo4j_client import Neo4jClient
from src.embeddings.text import event_text
from src.graph.correlation import EventCorrelationEngine
from src.memory.retrieval import MemoryRetrievalService
from src.orchestration.issues import IssueGenerator
from src.orchestration.timeline import TimelineEngine
from src.services.decision_extractor import DecisionExtractor
from src.services.graph_builder import GraphBuilder
from src.utils.logger import get_logger

logger = get_logger("nexus-ai.workflow")


class IntelligenceState(TypedDict, total=False):
    event: dict[str, Any]
    classification: dict[str, Any]
    context: dict[str, Any]
    related_decisions: list[dict[str, Any]]
    extraction: dict[str, Any]
    conflicts: list[dict[str, Any]]
    recommendations: list[dict[str, Any]]
    issues: list[dict[str, Any]]
    timeline: list[dict[str, Any]]
    correlation: dict[str, Any]
    graph_updates: list[str]
    metrics: dict[str, float]
    stored: bool
    error: str | None
    retries: int
    start_time: float


class IntelligenceWorkflow:
    """Phase 2 modular LangGraph orchestration workflow."""

    def __init__(
        self,
        extractor: DecisionExtractor,
        memory: MemoryRetrievalService,
        conflict_engine: AdvancedConflictEngine,
        graph_builder: GraphBuilder,
        neo4j: Neo4jClient,
        mongodb: MongoDBClient,
    ):
        self._extractor = extractor
        self._memory = memory
        self._conflict = conflict_engine
        self._graph_builder = graph_builder
        self._neo4j = neo4j
        self._mongodb = mongodb
        self._timeline = TimelineEngine()
        self._correlator = EventCorrelationEngine()
        self._issues = IssueGenerator()
        self._app = self._build()

    def _build(self):
        builder = StateGraph(IntelligenceState)
        builder.add_node("classify_event", self._classify_event)
        builder.add_node("retrieve_memory", self._retrieve_memory)
        builder.add_node("query_graph", self._query_graph)
        builder.add_node("reason_extract", self._reason_extract)
        builder.add_node("detect_conflicts", self._detect_conflicts)
        builder.add_node("generate_recommendations", self._generate_recommendations)
        builder.add_node("store_memory_graph", self._store_memory_graph)
        builder.add_node("retry_context", self._retry_context)
        builder.add_node("publish_ready", self._publish_ready)

        builder.set_entry_point("classify_event")
        builder.add_edge("classify_event", "retrieve_memory")
        builder.add_conditional_edges(
            "retrieve_memory",
            self._needs_context_retry,
            {"retry": "retry_context", "ok": "query_graph"},
        )
        builder.add_edge("retry_context", "query_graph")
        builder.add_edge("query_graph", "reason_extract")
        builder.add_edge("reason_extract", "detect_conflicts")
        builder.add_conditional_edges(
            "detect_conflicts",
            self._has_conflicts,
            {"conflict": "generate_recommendations", "clean": "store_memory_graph"},
        )
        builder.add_edge("generate_recommendations", "store_memory_graph")
        builder.add_edge("store_memory_graph", "publish_ready")
        builder.add_edge("publish_ready", END)
        return builder.compile()

    async def _classify_event(self, state: IntelligenceState) -> dict:
        event = state["event"]
        payload = event.get("payload", {})
        text = event_text(event).lower()
        classification = {
            "source": event.get("source"),
            "type": event.get("type"),
            "actor": payload.get("user", "unknown"),
            "implementation_related": any(k in text for k in ["commit", "diff", "config", "=", "deploy"]),
            "security_related": any(k in text for k in ["auth", "token", "secret", "rate limit", "encryption"]),
        }
        logger.info(f"[P2 1/9] Classified {event.get('event_id', '')[:12]} as {classification['type']}")
        return {"classification": classification}

    async def _retrieve_memory(self, state: IntelligenceState) -> dict:
        ctx = await self._memory.retrieve_context(state["event"], limit=8)
        metrics = state.get("metrics", {})
        metrics["retrieval_ms"] = ctx["latency_ms"]
        logger.info(f"[P2 2/9] Retrieved {len(ctx['items'])} contextual memories")
        return {"context": ctx, "metrics": metrics}

    def _needs_context_retry(self, state: IntelligenceState) -> str:
        if len(state.get("context", {}).get("items", [])) == 0 and state.get("retries", 0) < 1:
            return "retry"
        return "ok"

    async def _retry_context(self, state: IntelligenceState) -> dict:
        logger.info("[P2 retry] Context was sparse; continuing with graph-first reasoning")
        return {"retries": state.get("retries", 0) + 1}

    async def _query_graph(self, state: IntelligenceState) -> dict:
        started = time.perf_counter()
        related = await self._neo4j.find_related_context(event_text(state["event"]), limit=8)
        metrics = state.get("metrics", {})
        metrics["graph_query_ms"] = round((time.perf_counter() - started) * 1000, 2)
        logger.info(f"[P2 3/9] Graph context returned {len(related)} item(s)")
        return {"related_decisions": related, "metrics": metrics}

    async def _reason_extract(self, state: IntelligenceState) -> dict:
        extraction = await self._extractor.extract(state["event"])
        logger.info(f"[P2 4/9] Reasoning extraction decision={extraction.get('has_decision')}")
        return {"extraction": extraction}

    async def _detect_conflicts(self, state: IntelligenceState) -> dict:
        result = await self._conflict.analyze(
            state["event"],
            state.get("extraction", {}),
            state.get("context", {}).get("items", []),
            state.get("related_decisions", []),
        )
        metrics = state.get("metrics", {})
        metrics["conflict_detection_ms"] = result["latency_ms"]
        logger.info(f"[P2 5/9] Conflict analysis produced {len(result['conflicts'])} finding(s)")
        return {"conflicts": result["conflicts"], "metrics": metrics}

    def _has_conflicts(self, state: IntelligenceState) -> str:
        return "conflict" if state.get("conflicts") else "clean"

    async def _generate_recommendations(self, state: IntelligenceState) -> dict:
        recommendations = []
        issues = []
        for conflict in state.get("conflicts", []):
            rec = {
                "recommendation_id": str(uuid4()),
                "title": "Review conflicting implementation",
                "summary": conflict.get("recommendation", "Review drift against prior decision."),
                "action": "Open remediation task and block merge until owner approval.",
                "priority": "urgent" if conflict.get("severity") == "critical" else "high",
            }
            recommendations.append(rec)
            issues.append(self._issues.build_issue(state["event"], conflict, state.get("context", {}).get("items", [])))
        logger.info(f"[P2 6/9] Generated {len(recommendations)} recommendation(s)")
        return {"recommendations": recommendations, "issues": issues}

    async def _store_memory_graph(self, state: IntelligenceState) -> dict:
        started = time.perf_counter()
        event = state["event"]
        extraction = state.get("extraction", {})
        graph_updates = []

        await self._memory.store_event_memory(event, extraction)
        if extraction.get("has_decision") and extraction.get("confidence", 0) > 0.3:
            decision_id = await self._graph_builder.process_decision(event, extraction)
            graph_updates.append(f"decision:{decision_id}")
            if extraction.get("constraint"):
                await self._neo4j.create_architecture_constraint(
                    constraint_id=f"ac-{decision_id}",
                    text=extraction["constraint"],
                    category=extraction.get("category", "General"),
                    decision_id=decision_id,
                )
        else:
            await self._graph_builder.process_raw_event(event)

        for conflict in state.get("conflicts", []):
            await self._graph_builder.process_conflict(conflict)
            await self._neo4j.create_incident_for_conflict(conflict, event.get("event_id"))
            graph_updates.append(f"conflict:{conflict.get('conflict_id')}")

        for rec in state.get("recommendations", []):
            linked_conflict = state.get("conflicts", [{}])[0].get("conflict_id") if state.get("conflicts") else None
            await self._neo4j.create_recommendation(rec, linked_conflict)
            graph_updates.append(f"recommendation:{rec.get('recommendation_id')}")

        correlation = self._correlator.correlate(
            event,
            extraction,
            state.get("context", {}).get("items", []),
            state.get("conflicts", []),
        )
        for link in correlation.get("links", []):
            await self._neo4j.create_inferred_relationship(
                link["source_event_id"],
                link["target_id"],
                link["relationship"],
                link["score"],
                link["reason"],
            )

        timeline = self._timeline.build_entries(event, extraction, state.get("conflicts", []), state.get("recommendations", []))
        for entry in timeline:
            await self._mongodb.insert_timeline_event(entry)
            await self._neo4j.create_timeline_event(entry)

        for issue in state.get("issues", []):
            await self._mongodb.insert_generated_issue(issue)

        if extraction.get("has_decision"):
            await self._mongodb.insert_decision(extraction)

        metrics = state.get("metrics", {})
        metrics["graph_update_ms"] = round((time.perf_counter() - started) * 1000, 2)
        logger.info(f"[P2 7/9] Stored memory, graph, issues, and timeline")
        return {
            "stored": True,
            "timeline": timeline,
            "correlation": correlation,
            "graph_updates": graph_updates,
            "metrics": metrics,
        }

    async def _publish_ready(self, state: IntelligenceState) -> dict:
        elapsed_ms = round((time.perf_counter() - state.get("start_time", time.perf_counter())) * 1000, 2)
        metrics = state.get("metrics", {})
        metrics["total_processing_ms"] = elapsed_ms
        await self._mongodb.insert_processing_log({
            "event_id": state["event"].get("event_id"),
            "correlation_id": state["event"].get("correlation_id"),
            "stage": "phase2_intelligence_workflow",
            "status": "success",
            "duration_ms": elapsed_ms,
            "conflicts_found": len(state.get("conflicts", [])),
        })
        logger.info(f"[P2 8/9] Workflow complete in {elapsed_ms}ms")
        return {"metrics": metrics}

    async def process_event(self, event: dict[str, Any]) -> dict[str, Any]:
        initial: IntelligenceState = {
            "event": event,
            "classification": {},
            "context": {"items": [], "latency_ms": 0.0},
            "related_decisions": [],
            "extraction": {},
            "conflicts": [],
            "recommendations": [],
            "issues": [],
            "timeline": [],
            "correlation": {},
            "graph_updates": [],
            "metrics": {},
            "stored": False,
            "error": None,
            "retries": 0,
            "start_time": time.perf_counter(),
        }
        try:
            result = await self._app.ainvoke(initial)
            return {
                "event_id": event.get("event_id"),
                "correlation_id": event.get("correlation_id", event.get("event_id")),
                "stored": result.get("stored", False),
                "extraction": result.get("extraction", {}),
                "context": result.get("context", {}).get("items", []),
                "conflicts": result.get("conflicts", []),
                "recommendations": result.get("recommendations", []),
                "issues": result.get("issues", []),
                "timeline": result.get("timeline", []),
                "correlation": result.get("correlation", {}),
                "graph_updates": result.get("graph_updates", []),
                "metrics": result.get("metrics", {}),
            }
        except Exception as exc:
            logger.error(f"Phase 2 workflow failed: {exc}")
            return {
                "event_id": event.get("event_id"),
                "correlation_id": event.get("correlation_id", event.get("event_id")),
                "stored": False,
                "error": str(exc),
                "conflicts": [],
                "recommendations": [],
                "timeline": [],
                "graph_updates": [],
                "metrics": {},
            }
