from __future__ import annotations

from typing import Any
from uuid import uuid4

from src.embeddings.text import summarize_event


class TimelineEngine:
    """Reconstructs chronological event flows for frontend visualization later."""

    def build_entries(
        self,
        event: dict[str, Any],
        extraction: dict[str, Any],
        conflicts: list[dict[str, Any]],
        recommendations: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        correlation_id = event.get("correlation_id", event.get("event_id"))
        entries = [{
            "timeline_id": str(uuid4()),
            "event_id": event.get("event_id"),
            "correlation_id": correlation_id,
            "kind": self._kind(event, extraction),
            "summary": summarize_event(event),
            "timestamp": event.get("timestamp"),
            "source": event.get("source"),
        }]

        for conflict in conflicts:
            entries.append({
                "timeline_id": str(uuid4()),
                "event_id": event.get("event_id"),
                "correlation_id": correlation_id,
                "kind": "production_conflict",
                "summary": conflict.get("reasoning") or conflict.get("message", "Conflict detected"),
                "timestamp": event.get("timestamp"),
                "source": "ai-service",
                "severity": conflict.get("severity"),
            })

        for rec in recommendations:
            entries.append({
                "timeline_id": str(uuid4()),
                "event_id": event.get("event_id"),
                "correlation_id": correlation_id,
                "kind": "ai_recommendation",
                "summary": rec.get("summary", rec.get("title", "")),
                "timestamp": event.get("timestamp"),
                "source": "ai-service",
                "priority": rec.get("priority"),
            })
        return entries

    def _kind(self, event: dict[str, Any], extraction: dict[str, Any]) -> str:
        if extraction.get("has_decision"):
            return "architecture_decision"
        if event.get("source") == "slack":
            return "slack_discussion"
        if event.get("source") == "jira":
            return "jira_task"
        if event.get("source") == "github":
            return "github_commit"
        return "event"
