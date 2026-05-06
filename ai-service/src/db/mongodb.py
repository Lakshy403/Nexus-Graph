# ============================================
# Nexus-Graph AI Service — MongoDB Async Client
# ============================================
# Uses Motor (async pymongo) for non-blocking
# storage of extracted decisions, events, and
# processing logs.
# ============================================

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from src.config import get_settings
from src.utils.logger import get_logger

logger = get_logger("nexus-ai.mongodb")


class MongoDBClient:
    """Async MongoDB client for the AI service."""

    def __init__(self):
        self._client: Optional[AsyncIOMotorClient] = None
        self._db: Optional[AsyncIOMotorDatabase] = None

    async def connect(self) -> None:
        settings = get_settings()
        self._client = AsyncIOMotorClient(settings.mongodb_uri)
        self._db = self._client[settings.mongodb_db_name]
        # Verify connectivity
        await self._client.admin.command("ping")
        logger.info("✅ MongoDB connected", extra={"meta": {"db": settings.mongodb_db_name}})

    async def disconnect(self) -> None:
        if self._client:
            self._client.close()
            logger.info("MongoDB connection closed")

    @property
    def db(self) -> AsyncIOMotorDatabase:
        if self._db is None:
            raise RuntimeError("MongoDB not connected — call connect() first")
        return self._db

    # ---- Raw Events ----

    async def insert_raw_event(self, event: dict[str, Any]) -> str:
        result = await self.db.raw_events.insert_one({
            **event,
            "ingested_at": datetime.now(timezone.utc),
        })
        logger.debug("Raw event persisted", extra={"meta": {"id": str(result.inserted_id)}})
        return str(result.inserted_id)

    # ---- Extracted Decisions ----

    async def insert_decision(self, decision: dict[str, Any]) -> str:
        result = await self.db.extracted_decisions.insert_one({
            **decision,
            "created_at": datetime.now(timezone.utc),
        })
        logger.event("Decision stored in MongoDB", meta={"id": str(result.inserted_id)})
        return str(result.inserted_id)

    async def get_recent_decisions(self, limit: int = 50) -> list[dict]:
        cursor = (
            self.db.extracted_decisions
            .find({})
            .sort("created_at", -1)
            .limit(limit)
        )
        docs = await cursor.to_list(length=limit)
        for doc in docs:
            doc["_id"] = str(doc["_id"])
        return docs

    async def find_decisions_by_category(self, category: str) -> list[dict]:
        cursor = self.db.extracted_decisions.find({"category": category})
        docs = await cursor.to_list(length=100)
        for doc in docs:
            doc["_id"] = str(doc["_id"])
        return docs

    # ---- Processing Logs ----

    async def insert_processing_log(self, log: dict[str, Any]) -> str:
        result = await self.db.processing_logs.insert_one({
            **log,
            "created_at": datetime.now(timezone.utc),
        })
        return str(result.inserted_id)

    async def insert_generated_issue(self, issue: dict[str, Any]) -> str:
        result = await self.db.generated_issues.insert_one({
            **issue,
            "created_at": datetime.now(timezone.utc),
        })
        logger.event("Generated issue stored", meta={"id": str(result.inserted_id)})
        return str(result.inserted_id)

    async def insert_timeline_event(self, event: dict[str, Any]) -> str:
        result = await self.db.timeline_events.insert_one({
            **event,
            "created_at": datetime.now(timezone.utc),
        })
        return str(result.inserted_id)

    async def get_timeline(self, correlation_id: str, limit: int = 50) -> list[dict]:
        cursor = (
            self.db.timeline_events
            .find({"correlation_id": correlation_id})
            .sort("timestamp", 1)
            .limit(limit)
        )
        docs = await cursor.to_list(length=limit)
        for doc in docs:
            doc["_id"] = str(doc["_id"])
        return docs

    # ---- Statistics ----

    async def get_stats(self) -> dict[str, int]:
        raw = await self.db.raw_events.count_documents({})
        decisions = await self.db.extracted_decisions.count_documents({})
        logs = await self.db.processing_logs.count_documents({})
        issues = await self.db.generated_issues.count_documents({})
        timeline = await self.db.timeline_events.count_documents({})
        return {
            "raw_events": raw,
            "extracted_decisions": decisions,
            "processing_logs": logs,
            "generated_issues": issues,
            "timeline_events": timeline,
        }
