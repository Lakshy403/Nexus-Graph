from __future__ import annotations

import asyncio
import json
from concurrent import futures
from typing import Any, Callable, Awaitable

import grpc

from src.config import get_settings
from src.utils.logger import get_logger

logger = get_logger("nexus-ai.grpc")
nexus_pb2 = None
nexus_pb2_grpc = None


def _load_generated_modules():
    global nexus_pb2, nexus_pb2_grpc
    if nexus_pb2 is None or nexus_pb2_grpc is None:
        from src.generated import nexus_pb2 as _nexus_pb2
        from src.generated import nexus_pb2_grpc as _nexus_pb2_grpc
        nexus_pb2 = _nexus_pb2
        nexus_pb2_grpc = _nexus_pb2_grpc


class NexusIntelligenceServicer:
    def __init__(self, handler: Callable[[dict[str, Any]], Awaitable[dict[str, Any]]]):
        self._handler = handler

    async def AnalyzeEvent(self, request, context):
        event = self._event_from_request(request)
        result = await self._handler(event) or {"event_id": event["event_id"], "correlation_id": event["correlation_id"], "stored": False}
        return self._to_result(result)

    async def StreamAnalyzeEvent(self, request, context):
        event = self._event_from_request(request)
        yield nexus_pb2.AnalysisStreamChunk(
            event_id=event["event_id"],
            correlation_id=event["correlation_id"],
            stage="received",
            message="Event accepted by AI gRPC server",
        )
        yield nexus_pb2.AnalysisStreamChunk(
            event_id=event["event_id"],
            correlation_id=event["correlation_id"],
            stage="orchestrating",
            message="Running LangGraph intelligence workflow",
        )
        result = await self._handler(event) or {"event_id": event["event_id"], "correlation_id": event["correlation_id"], "stored": False}
        yield nexus_pb2.AnalysisStreamChunk(
            event_id=event["event_id"],
            correlation_id=event["correlation_id"],
            stage="complete",
            message="AI analysis complete",
            result=self._to_result(result),
        )

    def _event_from_request(self, request) -> dict[str, Any]:
        try:
            payload = json.loads(request.payload_json or "{}")
        except json.JSONDecodeError:
            payload = {"raw": request.payload_json}
        return {
            "event_id": request.event_id,
            "type": request.type,
            "source": request.source,
            "timestamp": request.timestamp,
            "correlation_id": request.correlation_id or request.event_id,
            "payload": payload,
            "metadata": dict(request.metadata),
        }

    def _to_result(self, result: dict[str, Any]):
        conflicts = [
            nexus_pb2.ConflictFinding(
                conflict_id=c.get("conflict_id", ""),
                type=c.get("type", ""),
                severity=c.get("severity", ""),
                confidence=float(c.get("confidence", 0.0)),
                reasoning=c.get("reasoning", c.get("message", "")),
                recommendation=c.get("recommendation", ""),
                related_decision_id=c.get("related_decision_id", c.get("conflicting_decision_id", "")),
            )
            for c in result.get("conflicts", [])
        ]
        recommendations = [
            nexus_pb2.Recommendation(
                recommendation_id=r.get("recommendation_id", ""),
                title=r.get("title", ""),
                summary=r.get("summary", ""),
                action=r.get("action", ""),
                priority=r.get("priority", ""),
            )
            for r in result.get("recommendations", [])
        ]
        context_items = [
            nexus_pb2.ContextItem(
                id=i.get("id", ""),
                kind=i.get("kind", ""),
                summary=i.get("summary", ""),
                score=float(i.get("score", 0.0)),
                metadata={k: str(v) for k, v in (i.get("metadata") or {}).items()},
            )
            for i in result.get("context", [])
        ]
        timeline = [
            nexus_pb2.TimelineEntry(
                timeline_id=t.get("timeline_id", ""),
                event_id=t.get("event_id", ""),
                kind=t.get("kind", ""),
                summary=t.get("summary", ""),
                timestamp=t.get("timestamp", ""),
                correlation_id=t.get("correlation_id", ""),
            )
            for t in result.get("timeline", [])
        ]
        return nexus_pb2.AIAnalysisResult(
            event_id=result.get("event_id", ""),
            correlation_id=result.get("correlation_id", ""),
            status="stored" if result.get("stored") else "failed",
            decision_json=json.dumps(result.get("extraction", {}), default=str),
            context=context_items,
            conflicts=conflicts,
            recommendations=recommendations,
            timeline=timeline,
            graph_updates=result.get("graph_updates", []),
            metrics={k: float(v) for k, v in result.get("metrics", {}).items()},
        )


class GrpcServerHandle:
    def __init__(self, server: grpc.aio.Server):
        self.server = server

    async def stop(self) -> None:
        await self.server.stop(grace=3)
        logger.info("gRPC server stopped")


async def start_grpc_server(handler: Callable[[dict[str, Any]], Awaitable[dict[str, Any]]]) -> GrpcServerHandle:
    _load_generated_modules()
    settings = get_settings()
    server = grpc.aio.server(futures.ThreadPoolExecutor(max_workers=8))
    nexus_pb2_grpc.add_NexusIntelligenceServicer_to_server(NexusIntelligenceServicer(handler), server)
    bind = f"{settings.ai_grpc_host}:{settings.ai_grpc_port}"
    server.add_insecure_port(bind)
    await server.start()
    logger.info(f"gRPC server listening on {bind}")
    return GrpcServerHandle(server)
