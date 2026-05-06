from __future__ import annotations

import re
from typing import Any

from src.embeddings.text import event_text


class EventCorrelationEngine:
    """Infers cross-tool relationships and scores their strength."""

    def correlate(
        self,
        event: dict[str, Any],
        extraction: dict[str, Any],
        context: list[dict[str, Any]],
        conflicts: list[dict[str, Any]],
    ) -> dict[str, Any]:
        text = event_text(event).lower()
        tokens = set(re.findall(r"[a-z0-9_/-]{3,}", text))
        links = []
        for item in context:
            summary = (item.get("summary") or "").lower()
            item_tokens = set(re.findall(r"[a-z0-9_/-]{3,}", summary))
            overlap = tokens & item_tokens
            score = min(0.95, 0.35 + (len(overlap) * 0.08) + float(item.get("score", 0)) * 0.25)
            if score >= 0.5:
                links.append({
                    "source_event_id": event.get("event_id"),
                    "target_id": item.get("id", ""),
                    "relationship": "HISTORICALLY_LINKED",
                    "score": round(score, 3),
                    "reason": f"Shared terms: {', '.join(sorted(list(overlap))[:6])}",
                })

        for conflict in conflicts:
            if conflict.get("related_decision_id"):
                links.append({
                    "source_event_id": event.get("event_id"),
                    "target_id": conflict["related_decision_id"],
                    "relationship": "VIOLATES",
                    "score": conflict.get("confidence", 0.8),
                    "reason": conflict.get("reasoning", "Conflict with historical decision"),
                })

        return {
            "correlation_id": event.get("correlation_id", event.get("event_id")),
            "links": links,
            "chain_hint": self._chain_hint(event, extraction, conflicts),
        }

    def _chain_hint(self, event: dict[str, Any], extraction: dict[str, Any], conflicts: list[dict[str, Any]]) -> str:
        if conflicts:
            return "Conversation -> Decision -> Task -> Commit -> Conflict -> Recommendation"
        if extraction.get("has_decision"):
            return "Conversation -> Decision"
        if event.get("source") == "github":
            return "Task -> Commit"
        return "Conversation"
