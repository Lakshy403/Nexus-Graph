# ============================================
# Nexus-Graph AI Service — Conflict Detector
# ============================================
# Rule-based conflict detection that compares
# incoming events against stored decisions and
# constraints in Neo4j / MongoDB.
# ============================================

from __future__ import annotations
import re
from typing import Any
from uuid import uuid4
from src.db.neo4j_client import Neo4jClient
from src.db.chromadb_client import ChromaDBClient
from src.utils.logger import get_logger

logger = get_logger("nexus-ai.conflict")


class ConflictDetector:
    """Detects conflicts between new events and existing decisions."""

    def __init__(self, neo4j: Neo4jClient, chromadb: ChromaDBClient):
        self._neo4j = neo4j
        self._chromadb = chromadb

    async def check_conflicts(self, event: dict[str, Any],
                              extraction: dict[str, Any]) -> list[dict[str, Any]]:
        conflicts = []
        event_type = event.get("type", "")
        payload = event.get("payload", {})
        text = (payload.get("message") or payload.get("diff")
                or payload.get("description") or "")

        # Get existing constraints from Neo4j
        existing_constraints = await self._neo4j.get_decision_constraints()

        # Run rule-based checks
        for constraint_rec in existing_constraints:
            conflict = self._check_rule_violation(
                text, event_type, constraint_rec, event.get("event_id", "")
            )
            if conflict:
                conflicts.append(conflict)

        # Semantic similarity check via ChromaDB
        if text:
            semantic_conflicts = await self._check_semantic_conflicts(text, event)
            conflicts.extend(semantic_conflicts)

        if conflicts:
            logger.warning(f"⚠️  {len(conflicts)} conflict(s) detected for event {event.get('event_id', '')[:12]}")
        return conflicts

    def _check_rule_violation(self, text: str, event_type: str,
                              constraint_rec: dict, event_id: str) -> dict[str, Any] | None:
        text_lower = text.lower()
        constraint = constraint_rec.get("constraint", "")
        decision = constraint_rec.get("decision", "")
        decision_id = constraint_rec.get("id", "")

        # --- Rule 1: Numeric threshold violations ---
        # Extract numbers from constraint (e.g. "180" from "Max temperature = 180°C")
        constraint_nums = re.findall(r'(\d+)', constraint)
        text_nums = re.findall(r'(\d+)', text)

        if constraint_nums and text_nums:
            for c_num in constraint_nums:
                for t_num in text_nums:
                    c_val, t_val = int(c_num), int(t_num)
                    # If the text sets a value higher than the constrained max
                    if t_val > c_val and any(kw in text_lower for kw in
                        ["limit", "temp", "max", "update", "set", "change", "="]):
                        return {
                            "conflict_id": str(uuid4()),
                            "type": "decision_drift",
                            "severity": "high",
                            "message": (f"Value {t_val} in incoming event exceeds "
                                        f"constraint '{constraint}' from decision: {decision[:80]}"),
                            "incoming_event_id": event_id,
                            "conflicting_decision_id": decision_id,
                            "incoming_summary": text[:200],
                            "existing_decision": decision,
                            "existing_constraint": constraint,
                        }

        # --- Rule 2: Deprecated technology usage ---
        deprecated_patterns = [
            (r'basic[_\-\s]?auth', "OAuth2", "basic auth"),
            (r'docker\s*swarm', "Kubernetes", "Docker Swarm"),
        ]
        for pattern, replacement, label in deprecated_patterns:
            if re.search(pattern, text_lower):
                constraint_lower = constraint.lower() + " " + decision.lower()
                if replacement.lower() in constraint_lower or label.lower() in constraint_lower:
                    return {
                        "conflict_id": str(uuid4()),
                        "type": "deprecated_usage",
                        "severity": "high",
                        "message": (f"Event uses deprecated '{label}' which conflicts "
                                    f"with decision to use '{replacement}'"),
                        "incoming_event_id": event_id,
                        "conflicting_decision_id": decision_id,
                        "incoming_summary": text[:200],
                        "existing_decision": decision,
                        "existing_constraint": constraint,
                    }

        # --- Rule 3: Removal of required features ---
        removal_kw = ["remove", "removed", "disable", "disabled", "delete"]
        required_kw = ["rate limit", "auth", "encryption", "logging"]
        if any(r in text_lower for r in removal_kw):
            for req in required_kw:
                if req in text_lower and req in (decision.lower() + " " + constraint.lower()):
                    return {
                        "conflict_id": str(uuid4()),
                        "type": "policy_violation",
                        "severity": "critical",
                        "message": f"Event removes required feature '{req}' mandated by existing decision",
                        "incoming_event_id": event_id,
                        "conflicting_decision_id": decision_id,
                        "incoming_summary": text[:200],
                        "existing_decision": decision,
                        "existing_constraint": constraint,
                    }

        return None

    async def _check_semantic_conflicts(self, text: str,
                                        event: dict[str, Any]) -> list[dict[str, Any]]:
        """Use ChromaDB similarity to find potentially contradicting past decisions."""
        conflicts = []
        try:
            similar = await self._chromadb.search_similar(text, n_results=3)
            for match in similar:
                distance = match.get("distance", 1.0)
                # Very close semantically but from a different source could indicate conflict
                if distance is not None and distance < 0.3:
                    doc = match.get("document", "")
                    # Simple heuristic: if similar text exists but has contradicting numbers
                    doc_nums = set(re.findall(r'\d+', doc))
                    text_nums = set(re.findall(r'\d+', text))
                    if doc_nums and text_nums and doc_nums != text_nums:
                        overlap = doc_nums & text_nums
                        diff = text_nums - doc_nums
                        if diff:
                            conflicts.append({
                                "conflict_id": str(uuid4()),
                                "type": "semantic_drift",
                                "severity": "medium",
                                "message": f"Semantically similar content found with different values: {diff}",
                                "incoming_event_id": event.get("event_id", ""),
                                "conflicting_decision_id": match.get("id"),
                                "incoming_summary": text[:200],
                                "existing_decision": doc[:200],
                            })
        except Exception as e:
            logger.debug(f"Semantic conflict check skipped: {e}")
        return conflicts
