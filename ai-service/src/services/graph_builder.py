# ============================================
# Nexus-Graph AI Service — Graph Builder
# ============================================
# Orchestrates writing extracted data into Neo4j
# and ChromaDB from pipeline outputs.
# ============================================

from __future__ import annotations
from typing import Any
from uuid import uuid4
from src.db.neo4j_client import Neo4jClient
from src.db.chromadb_client import ChromaDBClient
from src.utils.logger import get_logger

logger = get_logger("nexus-ai.graph_builder")


class GraphBuilder:
    """Translates extracted decisions and events into graph nodes + embeddings."""

    def __init__(self, neo4j: Neo4jClient, chromadb: ChromaDBClient):
        self._neo4j = neo4j
        self._chromadb = chromadb

    async def process_decision(self, event: dict[str, Any],
                               extraction: dict[str, Any]) -> str:
        """Create graph nodes for an extracted decision and store embedding."""
        decision_id = str(uuid4())
        source_user = extraction.get("source_user", "unknown")
        decision_text = extraction.get("decision", "")
        constraint = extraction.get("constraint", "")
        category = extraction.get("category", "General")
        importance = extraction.get("importance", "medium")

        # 1. Merge person node
        await self._neo4j.merge_person(source_user)

        # 2. Create decision node + MADE_DECISION relationship
        await self._neo4j.create_decision(
            decision_id=decision_id,
            decision_text=decision_text,
            constraint=constraint,
            category=category,
            importance=importance,
            source_user=source_user,
        )

        # 3. If Jira ticket, also create a Task node + LINKED_TO
        event_type = event.get("type", "")
        payload = event.get("payload", {})
        if event_type in ("jira_ticket", "jira_comment"):
            ticket_id = payload.get("ticket_id", str(uuid4()))
            title = payload.get("title", "Untitled task")
            status = payload.get("status", "Open")
            await self._neo4j.create_task(ticket_id, title, status, decision_id)

        # 4. If GitHub commit, create Commit node
        if event_type in ("github_commit", "github_pr"):
            sha = payload.get("commit_sha", str(uuid4())[:12])
            msg = payload.get("message", "")
            repo = payload.get("repo", "unknown")
            branch = payload.get("branch", "main")
            author = payload.get("user", "unknown")
            await self._neo4j.create_commit(sha, msg, repo, branch, author, payload.get("ticket_id"))

        # 5. Store semantic embedding in ChromaDB
        embed_text = f"{decision_text}. {constraint}".strip(". ")
        if embed_text:
            await self._chromadb.store_decision_embedding(
                decision_id=decision_id,
                text=embed_text,
                metadata={
                    "category": category,
                    "importance": importance,
                    "source_user": source_user,
                    "event_id": event.get("event_id", ""),
                },
            )

        logger.info(f"✅ Graph built for decision {decision_id[:12]}")
        return decision_id

    async def process_conflict(self, conflict: dict[str, Any]) -> None:
        """Store a conflict node in Neo4j and link to the violated decision."""
        conflict_id = conflict.get("conflict_id", str(uuid4()))
        await self._neo4j.create_conflict(
            conflict_id=conflict_id,
            conflict_type=conflict.get("type", "decision_drift"),
            severity=conflict.get("severity", "medium"),
            message=conflict.get("message", ""),
            decision_id=conflict.get("conflicting_decision_id"),
        )

    async def process_raw_event(self, event: dict[str, Any]) -> None:
        """Create graph nodes for events that don't contain decisions
        (e.g. plain commits, ticket updates)."""
        event_type = event.get("type", "")
        payload = event.get("payload", {})
        user = payload.get("user", "unknown")

        await self._neo4j.merge_person(user)

        if event_type in ("github_commit", "github_pr"):
            sha = payload.get("commit_sha", str(uuid4())[:12])
            await self._neo4j.create_commit(
                sha=sha,
                message=payload.get("message", ""),
                repo=payload.get("repo", "unknown"),
                branch=payload.get("branch", "main"),
                author=user,
                linked_task_id=payload.get("ticket_id"),
            )

        if event_type in ("jira_ticket", "jira_comment"):
            ticket_id = payload.get("ticket_id", str(uuid4()))
            await self._neo4j.create_task(
                task_id=ticket_id,
                title=payload.get("title", ""),
                status=payload.get("status", "Open"),
            )
