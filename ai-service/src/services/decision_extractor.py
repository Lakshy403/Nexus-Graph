# ============================================
# Nexus-Graph AI Service — Decision Extractor
# ============================================
# Uses Google Gemini (via google-genai) to
# extract structured decisions and constraints
# from raw workplace event text.
# ============================================

from __future__ import annotations
import json, re
from typing import Any
from google import genai
from src.config import get_settings
from src.utils.logger import get_logger

logger = get_logger("nexus-ai.extractor")

EXTRACTION_PROMPT = """You are an AI analyst for an organizational memory system called Nexus-Graph.
Analyze the following workplace event and extract structured information.

EVENT TYPE: {event_type}
SOURCE: {source}
USER: {user}
TEXT: {text}

Extract the following as JSON (and ONLY valid JSON, no markdown fences):
{{
  "has_decision": true/false,
  "decision": "Clear statement of the decision made (empty string if none)",
  "constraint": "Any explicit constraint or limit mentioned (empty string if none)",
  "category": "One of: Infrastructure, Security, Engineering, DevOps, Frontend, Architecture, General",
  "importance": "One of: low, medium, high, critical",
  "keywords": ["list", "of", "relevant", "keywords"],
  "confidence": 0.0 to 1.0
}}

Rules:
- Only mark has_decision=true if there is a clear decision, directive, or policy statement
- Constraints are specific limits, thresholds, deadlines, or prohibitions
- Be conservative with importance — only critical for safety/security/production issues
- Keywords should capture technical terms and action items
"""

# Fallback keyword-based extraction when LLM is unavailable
DECISION_KEYWORDS = [
    "decision", "decided", "agreed", "must", "should", "will",
    "policy", "standard", "require", "enforce", "limit",
    "max", "min", "deadline", "constraint", "mandatory",
    "deprecated", "migrate", "no exceptions", "approved",
]

CATEGORY_KEYWORDS = {
    "Infrastructure": ["server", "cooling", "temperature", "hardware", "capacity", "datacenter"],
    "Security": ["auth", "rate limit", "encryption", "vulnerability", "access", "password"],
    "Engineering": ["code", "api", "service", "library", "framework", "react", "migration"],
    "DevOps": ["kubernetes", "docker", "deployment", "ci/cd", "pipeline", "swarm", "k8s"],
    "Frontend": ["ui", "frontend", "react", "css", "component", "design"],
    "Architecture": ["architecture", "microservice", "monolith", "pattern", "schema"],
}


class DecisionExtractor:
    """Extracts decisions from event text using Gemini LLM with keyword fallback."""

    def __init__(self):
        self._client = None
        self._model_name = "gemini-2.0-flash"

    def initialize(self) -> None:
        s = get_settings()
        if s.gemini_api_key:
            self._client = genai.Client(api_key=s.gemini_api_key)
            logger.info("✅ Gemini LLM client initialized")
        else:
            logger.warning("⚠️  No GEMINI_API_KEY — using keyword fallback extraction")

    async def extract(self, event: dict[str, Any]) -> dict[str, Any]:
        payload = event.get("payload", {})
        text = payload.get("message") or payload.get("description") or payload.get("title") or payload.get("diff") or ""
        user = payload.get("user", "unknown")
        event_type = event.get("type", "unknown")
        source = event.get("source", "unknown")

        if self._client:
            return await self._extract_with_llm(event_type, source, user, text, event.get("event_id", ""))
        else:
            return self._extract_with_keywords(event_type, source, user, text, event.get("event_id", ""))

    async def _extract_with_llm(self, event_type: str, source: str, user: str,
                                text: str, event_id: str) -> dict[str, Any]:
        prompt = EXTRACTION_PROMPT.format(event_type=event_type, source=source, user=user, text=text)
        try:
            response = self._client.models.generate_content(model=self._model_name, contents=prompt)
            raw = response.text.strip()
            # Strip markdown fences if present
            raw = re.sub(r'^```(?:json)?\s*', '', raw)
            raw = re.sub(r'\s*```$', '', raw)
            result = json.loads(raw)
            result["event_id"] = event_id
            result["source_user"] = user
            result["source_type"] = event_type
            result["raw_text"] = text
            logger.ai(f"LLM extraction complete for {event_id[:12]}",
                      meta=f"decision={result.get('has_decision')}")
            return result
        except Exception as e:
            logger.error(f"LLM extraction failed: {e}")
            return self._extract_with_keywords(event_type, source, user, text, event_id)

    def _extract_with_keywords(self, event_type: str, source: str, user: str,
                               text: str, event_id: str) -> dict[str, Any]:
        text_lower = text.lower()
        has_decision = any(kw in text_lower for kw in DECISION_KEYWORDS)

        # Determine category
        category = "General"
        for cat, keywords in CATEGORY_KEYWORDS.items():
            if any(kw in text_lower for kw in keywords):
                category = cat
                break

        # Extract constraint
        constraint = ""
        constraint_patterns = [
            r'(\d+)\s*°?[cCfF]', r'max\w*\s*[=:]\s*(\d+)',
            r'limit\w*\s*[=:]\s*(\d+)', r'(\d+)\s*req/min',
        ]
        for pattern in constraint_patterns:
            match = re.search(pattern, text)
            if match:
                constraint = match.group(0)
                break

        # Importance
        importance = "medium"
        if any(w in text_lower for w in ["critical", "no exceptions", "must", "mandatory"]):
            importance = "high"
        elif any(w in text_lower for w in ["deprecated", "agreed", "standardize"]):
            importance = "medium"

        # Keywords
        keywords = [kw for kw in DECISION_KEYWORDS if kw in text_lower]

        return {
            "has_decision": has_decision,
            "decision": text[:200] if has_decision else "",
            "constraint": constraint,
            "category": category,
            "importance": importance,
            "keywords": keywords[:10],
            "confidence": 0.6 if has_decision else 0.2,
            "event_id": event_id,
            "source_user": user,
            "source_type": event_type,
            "raw_text": text,
        }
