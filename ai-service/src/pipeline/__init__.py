# ============================================
# Nexus-Graph AI Service — LangGraph Pipeline
# ============================================
# Orchestrates the multi-step AI extraction flow:
#   1. Event Parsing
#   2. Context Analysis
#   3. Decision Extraction
#   4. Conflict Detection (Validation)
#   5. Storage Pipeline
# ============================================

from __future__ import annotations
import time
from typing import Any, TypedDict
from langgraph.graph import StateGraph, END
from src.services.decision_extractor import DecisionExtractor
from src.services.conflict_detector import ConflictDetector
from src.services.graph_builder import GraphBuilder
from src.db.mongodb import MongoDBClient
from src.utils.logger import get_logger

logger = get_logger("nexus-ai.pipeline")


class PipelineState(TypedDict, total=False):
    """State flowing through every LangGraph node."""
    event: dict[str, Any]
    source: str
    raw_text: str
    parsed_context: dict[str, Any]
    extraction: dict[str, Any]
    decisions_stored: list[str]
    conflicts: list[dict[str, Any]]
    validation_passed: bool
    stored: bool
    error: str | None
    start_time: float


class ExtractionPipeline:
    """LangGraph-orchestrated pipeline for processing workplace events."""

    def __init__(
        self,
        extractor: DecisionExtractor,
        conflict_detector: ConflictDetector,
        graph_builder: GraphBuilder,
        mongodb: MongoDBClient,
    ):
        self._extractor = extractor
        self._conflict = conflict_detector
        self._graph = graph_builder
        self._mongodb = mongodb
        self._graph_app = self._build_graph()

    def _build_graph(self):
        builder = StateGraph(PipelineState)

        builder.add_node("parse_event", self._parse_event)
        builder.add_node("analyze_context", self._analyze_context)
        builder.add_node("extract_decisions", self._extract_decisions)
        builder.add_node("validate_and_detect", self._validate_and_detect)
        builder.add_node("store_results", self._store_results)

        builder.set_entry_point("parse_event")
        builder.add_edge("parse_event", "analyze_context")
        builder.add_edge("analyze_context", "extract_decisions")
        builder.add_edge("extract_decisions", "validate_and_detect")
        builder.add_edge("validate_and_detect", "store_results")
        builder.add_edge("store_results", END)

        return builder.compile()

    # ---- Node 1: Event Parsing ----

    async def _parse_event(self, state: PipelineState) -> dict:
        event = state["event"]
        payload = event.get("payload", {})
        raw_text = (
            payload.get("message")
            or payload.get("description")
            or payload.get("title")
            or payload.get("diff")
            or ""
        )
        logger.info(f"[1/5] Parsing event {event.get('event_id', '')[:12]}…")
        return {
            "source": event.get("source", "unknown"),
            "raw_text": raw_text,
            "start_time": time.time(),
        }

    # ---- Node 2: Context Analysis ----

    async def _analyze_context(self, state: PipelineState) -> dict:
        event = state["event"]
        payload = event.get("payload", {})
        context = {
            "event_type": event.get("type", "unknown"),
            "user": payload.get("user", "unknown"),
            "channel": payload.get("channel"),
            "repo": payload.get("repo"),
            "branch": payload.get("branch"),
            "ticket_id": payload.get("ticket_id"),
            "has_diff": bool(payload.get("diff")),
            "text_length": len(state.get("raw_text", "")),
        }
        logger.info(f"[2/5] Context analyzed — type={context['event_type']}, user={context['user']}")
        return {"parsed_context": context}

    # ---- Node 3: Decision Extraction ----

    async def _extract_decisions(self, state: PipelineState) -> dict:
        event = state["event"]
        extraction = await self._extractor.extract(event)
        has_decision = extraction.get("has_decision", False)
        logger.info(
            f"[3/5] Extraction complete — decision={has_decision}, "
            f"confidence={extraction.get('confidence', 0):.2f}"
        )
        return {"extraction": extraction}

    # ---- Node 4: Validation + Conflict Detection ----

    async def _validate_and_detect(self, state: PipelineState) -> dict:
        event = state["event"]
        extraction = state.get("extraction", {})
        conflicts = await self._conflict.check_conflicts(event, extraction)
        validation_passed = extraction.get("has_decision", False) and extraction.get("confidence", 0) > 0.3
        logger.info(
            f"[4/5] Validation={'PASS' if validation_passed else 'SKIP'}, "
            f"conflicts={len(conflicts)}"
        )
        return {
            "conflicts": conflicts,
            "validation_passed": validation_passed,
        }

    # ---- Node 5: Storage Pipeline ----

    async def _store_results(self, state: PipelineState) -> dict:
        event = state["event"]
        extraction = state.get("extraction", {})
        conflicts = state.get("conflicts", [])
        decisions_stored = []

        try:
            # Store extraction in MongoDB
            if state.get("validation_passed") and extraction.get("has_decision"):
                await self._mongodb.insert_decision(extraction)
                # Build graph nodes
                decision_id = await self._graph.process_decision(event, extraction)
                decisions_stored.append(decision_id)
            else:
                # Still create basic graph nodes for non-decision events
                await self._graph.process_raw_event(event)

            # Store conflicts
            for conflict in conflicts:
                await self._graph.process_conflict(conflict)

            # Processing log
            elapsed = time.time() - state.get("start_time", time.time())
            await self._mongodb.insert_processing_log({
                "event_id": event.get("event_id"),
                "stage": "ai_pipeline",
                "status": "success",
                "duration_ms": round(elapsed * 1000, 2),
                "has_decision": extraction.get("has_decision", False),
                "conflicts_found": len(conflicts),
            })

            logger.info(
                f"[5/5] ✅ Stored — decisions={len(decisions_stored)}, "
                f"conflicts={len(conflicts)}, "
                f"elapsed={elapsed:.2f}s"
            )
            return {"stored": True, "decisions_stored": decisions_stored}

        except Exception as e:
            logger.error(f"[5/5] ❌ Storage failed: {e}")
            return {"stored": False, "error": str(e)}

    # ---- Public API ----

    async def process_event(self, event: dict[str, Any]) -> dict[str, Any]:
        """Run the full LangGraph pipeline on a single event."""
        initial_state: PipelineState = {
            "event": event,
            "source": "",
            "raw_text": "",
            "parsed_context": {},
            "extraction": {},
            "decisions_stored": [],
            "conflicts": [],
            "validation_passed": False,
            "stored": False,
            "error": None,
            "start_time": time.time(),
        }
        try:
            result = await self._graph_app.ainvoke(initial_state)
            return {
                "event_id": event.get("event_id"),
                "stored": result.get("stored", False),
                "decisions": result.get("decisions_stored", []),
                "conflicts": result.get("conflicts", []),
                "extraction": result.get("extraction", {}),
                "error": result.get("error"),
            }
        except Exception as e:
            logger.error(f"Pipeline failed for {event.get('event_id', 'unknown')}: {e}")
            return {
                "event_id": event.get("event_id"),
                "stored": False,
                "error": str(e),
            }
