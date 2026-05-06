# ============================================
# Nexus-Graph AI Service — Pydantic Schemas
# ============================================
# Defines all data models flowing through the
# extraction pipeline and stored in databases.
# ============================================

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


# ---- Enums ----

class EventType(str, Enum):
    SLACK_MESSAGE = "slack_message"
    GITHUB_COMMIT = "github_commit"
    GITHUB_PR = "github_pr"
    JIRA_TICKET = "jira_ticket"
    JIRA_COMMENT = "jira_comment"
    DECISION_EXTRACTED = "decision_extracted"
    CONFLICT_DETECTED = "conflict_detected"


class ImportanceLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ConflictSeverity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


# ---- Event Models ----

class EventPayload(BaseModel):
    """Flexible payload carried by every event."""
    user: str
    message: Optional[str] = None
    channel: Optional[str] = None
    repo: Optional[str] = None
    branch: Optional[str] = None
    diff: Optional[str] = None
    commit_sha: Optional[str] = None
    ticket_id: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None


class EventMetadata(BaseModel):
    processed: bool = False
    received_at: Optional[str] = None
    processing_time_ms: Optional[float] = None
    ai_version: Optional[str] = None


class NexusEvent(BaseModel):
    """Canonical event schema flowing through the system."""
    event_id: str
    type: str
    source: str
    timestamp: str
    payload: EventPayload
    metadata: EventMetadata = Field(default_factory=EventMetadata)


# ---- AI Extraction Models ----

class ExtractedDecision(BaseModel):
    """Structured output from the AI extraction pipeline."""
    event_id: str
    decision: str
    constraint: Optional[str] = None
    category: str = "General"
    importance: str = "medium"
    keywords: list[str] = Field(default_factory=list)
    source_user: str = ""
    source_type: str = ""
    source_channel: Optional[str] = None
    raw_text: str = ""
    confidence: float = 0.0
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ConflictReport(BaseModel):
    """Output when a conflict is detected between a new event and
    an existing decision stored in the knowledge graph."""
    conflict_id: Optional[str] = None
    type: str = "decision_drift"
    severity: str = "medium"
    message: str = ""
    incoming_event_id: str = ""
    conflicting_decision_id: Optional[str] = None
    incoming_summary: str = ""
    existing_decision: str = ""
    existing_constraint: Optional[str] = None
    detected_at: datetime = Field(default_factory=datetime.utcnow)


# ---- LangGraph Pipeline State ----

class PipelineState(BaseModel):
    """Mutable state passed through every LangGraph node."""
    event: dict[str, Any] = Field(default_factory=dict)
    source: str = ""
    raw_text: str = ""
    parsed_context: dict[str, Any] = Field(default_factory=dict)
    decisions: list[ExtractedDecision] = Field(default_factory=list)
    conflicts: list[ConflictReport] = Field(default_factory=list)
    validation_passed: bool = False
    stored: bool = False
    error: Optional[str] = None
    processing_time_ms: float = 0.0
