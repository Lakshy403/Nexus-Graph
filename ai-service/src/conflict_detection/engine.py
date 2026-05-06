from __future__ import annotations

import re
import time
from typing import Any
from uuid import uuid4

from src.embeddings.text import event_text
from src.utils.logger import get_logger

logger = get_logger("nexus-ai.conflict2")


class AdvancedConflictEngine:
    """Memory-aware decision drift analysis with explainable findings."""

    SECURITY = ["auth", "token", "oauth", "password", "encryption", "rate limit", "secret"]
    ARCHITECTURE = ["grpc", "rest", "microservice", "schema", "kafka", "redis", "dependency"]
    INFRA = ["cooling", "temperature", "server", "kubernetes", "docker", "capacity"]

    async def analyze(
        self,
        event: dict[str, Any],
        extraction: dict[str, Any],
        context_items: list[dict[str, Any]],
        graph_context: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        started = time.perf_counter()
        text = event_text(event).lower()
        findings: list[dict[str, Any]] = []

        candidates = context_items + (graph_context or [])
        for item in candidates:
            summary = (item.get("summary") or item.get("decision") or "").lower()
            finding = self._numeric_drift(text, summary, item)
            if finding:
                findings.append(finding)
                continue

            finding = self._semantic_policy_drift(text, summary, item)
            if finding:
                findings.append(finding)

        elapsed_ms = round((time.perf_counter() - started) * 1000, 2)
        if findings:
            logger.warning(f"Advanced conflict engine found {len(findings)} issue(s)")
        return {"conflicts": findings, "latency_ms": elapsed_ms}

    def _numeric_drift(self, text: str, memory: str, item: dict[str, Any]) -> dict[str, Any] | None:
        incoming_nums = [int(n) for n in re.findall(r"\d+", text)]
        memory_nums = [int(n) for n in re.findall(r"\d+", memory)]
        if not incoming_nums or not memory_nums:
            return None

        max_memory = max(memory_nums)
        max_incoming = max(incoming_nums)
        guarded = any(k in memory for k in ["max", "limit", "expire", "ttl", "req/min", "constraint"])
        implementation = any(k in text for k in ["=", "set", "update", "change", "expiry", "limit", "config"])
        if guarded and implementation and max_incoming > max_memory:
            conflict_type = self._classify_type(text + " " + memory)
            severity = "critical" if conflict_type == "security_conflict" else "high"
            return {
                "conflict_id": str(uuid4()),
                "type": "decision_drift" if conflict_type != "security_conflict" else conflict_type,
                "severity": severity,
                "confidence": 0.92,
                "reasoning": (
                    f"Incoming implementation value {max_incoming} exceeds historical constraint "
                    f"{max_memory}. The stored intent appears to be a maximum or policy boundary."
                ),
                "recommendation": "Revert the implementation value or open an explicit decision review.",
                "related_decision_id": item.get("id") or item.get("decision_id", ""),
                "evidence": item,
            }
        return None

    def _semantic_policy_drift(self, text: str, memory: str, item: dict[str, Any]) -> dict[str, Any] | None:
        checks = [
            ("basic auth", "oauth", "security_conflict", "critical"),
            ("docker swarm", "kubernetes", "architecture_conflict", "high"),
            ("remove rate limit", "rate limit", "policy_violation", "critical"),
            ("disable encryption", "encryption", "security_conflict", "critical"),
        ]
        for incoming, historical, ctype, severity in checks:
            if incoming in text and historical in memory:
                return {
                    "conflict_id": str(uuid4()),
                    "type": ctype,
                    "severity": severity,
                    "confidence": 0.88,
                    "reasoning": f"Incoming event contains '{incoming}' while historical context requires '{historical}'.",
                    "recommendation": "Create a remediation task and request owner approval before merging.",
                    "related_decision_id": item.get("id") or item.get("decision_id", ""),
                    "evidence": item,
                }
        return None

    def _classify_type(self, text: str) -> str:
        if any(k in text for k in self.SECURITY):
            return "security_conflict"
        if any(k in text for k in self.INFRA):
            return "infrastructure_conflict"
        if any(k in text for k in self.ARCHITECTURE):
            return "architecture_conflict"
        return "policy_violation"
