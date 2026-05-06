from __future__ import annotations

from typing import Any
from uuid import uuid4

from src.embeddings.text import summarize_event


class IssueGenerator:
    """Creates mock Jira-style issues for detected conflicts."""

    def build_issue(
        self,
        event: dict[str, Any],
        conflict: dict[str, Any],
        context: list[dict[str, Any]],
    ) -> dict[str, Any]:
        issue_id = f"MOCK-{str(uuid4())[:8].upper()}"
        severity = conflict.get("severity", "medium")
        return {
            "issue_id": issue_id,
            "type": "mock_jira_issue",
            "title": f"Conflict Detected: {conflict.get('type', 'Decision Drift').replace('_', ' ').title()}",
            "severity": severity,
            "source_event_id": event.get("event_id"),
            "correlation_id": event.get("correlation_id", event.get("event_id")),
            "body": {
                "conflicting_event": summarize_event(event),
                "reasoning": conflict.get("reasoning", conflict.get("message", "")),
                "contextual_evidence": context[:3],
                "affected_systems": self._affected_systems(event),
                "recommendation": conflict.get("recommendation", "Review the implementation against approved decisions."),
            },
            "status": "Open",
        }

    def _affected_systems(self, event: dict[str, Any]) -> list[str]:
        payload = event.get("payload", {})
        systems = [payload.get("repo"), payload.get("branch"), payload.get("channel"), payload.get("ticket_id")]
        return [s for s in systems if s]
