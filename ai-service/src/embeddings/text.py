from __future__ import annotations

from typing import Any


def event_text(event: dict[str, Any]) -> str:
    payload = event.get("payload", {})
    parts = [
        payload.get("message"),
        payload.get("title"),
        payload.get("description"),
        payload.get("diff"),
        payload.get("repo"),
        payload.get("branch"),
    ]
    return "\n".join(str(p) for p in parts if p).strip()


def summarize_event(event: dict[str, Any]) -> str:
    payload = event.get("payload", {})
    text = event_text(event)
    user = payload.get("user", "unknown")
    source = event.get("source", "unknown")
    event_type = event.get("type", "event")
    if text:
        return f"{event_type} from {source} by {user}: {text[:240]}"
    return f"{event_type} from {source} by {user}"
