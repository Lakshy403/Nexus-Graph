# ============================================
# Nexus-Graph AI Service — Neo4j Graph Client
# ============================================

from __future__ import annotations
from typing import Any, Optional
from neo4j import AsyncGraphDatabase, AsyncDriver
from src.config import get_settings
from src.utils.logger import get_logger

logger = get_logger("nexus-ai.neo4j")


class Neo4jClient:
    def __init__(self):
        self._driver: Optional[AsyncDriver] = None

    async def connect(self) -> None:
        s = get_settings()
        self._driver = AsyncGraphDatabase.driver(s.neo4j_uri, auth=(s.neo4j_user, s.neo4j_password))
        async with self._driver.session() as session:
            await (await session.run("RETURN 1 AS n")).single()
        logger.info("✅ Neo4j connected", extra={"meta": s.neo4j_uri})

    async def disconnect(self) -> None:
        if self._driver:
            await self._driver.close()

    async def merge_person(self, name: str, role: str = "Unknown") -> None:
        q = "MERGE (p:Person {name: $name}) ON CREATE SET p.role=$role, p.created_at=datetime()"
        async with self._driver.session() as s:
            await s.run(q, name=name, role=role)

    async def create_decision(self, decision_id: str, decision_text: str, constraint: str | None,
                              category: str, importance: str, source_user: str) -> None:
        q = """
        MERGE (d:Decision {decision_id: $did})
        ON CREATE SET d.text=$text, d.constraint=$con, d.category=$cat, d.importance=$imp, d.created_at=datetime()
        WITH d
        MERGE (p:Person {name: $user})
        MERGE (p)-[:MADE_DECISION {at: datetime()}]->(d)
        """
        async with self._driver.session() as s:
            await s.run(q, did=decision_id, text=decision_text, con=constraint or "", cat=category, imp=importance, user=source_user)
        logger.info(f"GRAPH Decision created → {decision_id[:12]}")

    async def create_task(self, task_id: str, title: str, status: str, linked_decision_id: str | None = None) -> None:
        q = "MERGE (t:Task {task_id: $tid}) ON CREATE SET t.title=$title, t.status=$status, t.created_at=datetime()"
        async with self._driver.session() as s:
            await s.run(q, tid=task_id, title=title, status=status)
        if linked_decision_id:
            lq = "MATCH (d:Decision {decision_id:$did}),(t:Task {task_id:$tid}) MERGE (d)-[:LINKED_TO]->(t)"
            async with self._driver.session() as s:
                await s.run(lq, did=linked_decision_id, tid=task_id)

    async def create_commit(self, sha: str, message: str, repo: str, branch: str, author: str,
                            linked_task_id: str | None = None) -> None:
        q = """
        MERGE (c:Commit {sha: $sha})
        ON CREATE SET c.message=$msg, c.repo=$repo, c.branch=$branch, c.created_at=datetime()
        WITH c MERGE (p:Person {name: $author}) MERGE (p)-[:AUTHORED]->(c)
        """
        async with self._driver.session() as s:
            await s.run(q, sha=sha, msg=message, repo=repo, branch=branch, author=author)
        if linked_task_id:
            lq = "MATCH (t:Task {task_id:$tid}),(c:Commit {sha:$sha}) MERGE (t)-[:IMPLEMENTED_BY]->(c)"
            async with self._driver.session() as s:
                await s.run(lq, tid=linked_task_id, sha=sha)

    async def create_architecture_constraint(self, constraint_id: str, text: str,
                                             category: str, decision_id: str | None = None) -> None:
        q = """
        MERGE (ac:ArchitectureConstraint {constraint_id: $cid})
        ON CREATE SET ac.text=$text, ac.category=$cat, ac.created_at=datetime()
        """
        async with self._driver.session() as s:
            await s.run(q, cid=constraint_id, text=text, cat=category)
        if decision_id:
            lq = """
            MATCH (d:Decision {decision_id:$did}), (ac:ArchitectureConstraint {constraint_id:$cid})
            MERGE (d)-[:RELATED_TO]->(ac)
            """
            async with self._driver.session() as s:
                await s.run(lq, did=decision_id, cid=constraint_id)

    async def create_recommendation(self, recommendation: dict[str, Any],
                                    conflict_id: str | None = None) -> None:
        q = """
        MERGE (r:Recommendation {recommendation_id: $rid})
        ON CREATE SET r.title=$title, r.summary=$summary, r.action=$action,
                      r.priority=$priority, r.created_at=datetime()
        """
        async with self._driver.session() as s:
            await s.run(
                q,
                rid=recommendation.get("recommendation_id"),
                title=recommendation.get("title", ""),
                summary=recommendation.get("summary", ""),
                action=recommendation.get("action", ""),
                priority=recommendation.get("priority", "medium"),
            )
        if conflict_id:
            lq = """
            MATCH (cf:Conflict {conflict_id:$cid}), (r:Recommendation {recommendation_id:$rid})
            MERGE (cf)-[:RECOMMENDED_FIX]->(r)
            """
            async with self._driver.session() as s:
                await s.run(lq, cid=conflict_id, rid=recommendation.get("recommendation_id"))

    async def create_timeline_event(self, entry: dict[str, Any]) -> None:
        q = """
        MERGE (te:TimelineEvent {timeline_id:$tid})
        ON CREATE SET te.event_id=$eid, te.kind=$kind, te.summary=$summary,
                      te.timestamp=$timestamp, te.correlation_id=$cid, te.created_at=datetime()
        """
        async with self._driver.session() as s:
            await s.run(
                q,
                tid=entry.get("timeline_id"),
                eid=entry.get("event_id"),
                kind=entry.get("kind"),
                summary=entry.get("summary", ""),
                timestamp=entry.get("timestamp", ""),
                cid=entry.get("correlation_id", ""),
            )

    async def create_incident_for_conflict(self, conflict: dict[str, Any],
                                           event_id: str | None = None) -> str:
        incident_id = f"inc-{conflict.get('conflict_id', '')[:12]}"
        q = """
        MERGE (i:Incident {incident_id:$iid})
        ON CREATE SET i.severity=$severity, i.summary=$summary, i.event_id=$eid, i.created_at=datetime()
        WITH i
        MATCH (cf:Conflict {conflict_id:$cid})
        MERGE (i)-[:CAUSED_BY]->(cf)
        """
        async with self._driver.session() as s:
            await s.run(
                q,
                iid=incident_id,
                severity=conflict.get("severity", "medium"),
                summary=conflict.get("reasoning", conflict.get("message", "")),
                eid=event_id or "",
                cid=conflict.get("conflict_id"),
            )
        return incident_id

    async def create_inferred_relationship(self, source_event_id: str, target_id: str,
                                           relationship: str, score: float, reason: str) -> None:
        q = """
        MERGE (e:TimelineEvent {event_id:$eid})
        ON CREATE SET e.timeline_id=$eid, e.kind='event_reference', e.created_at=datetime()
        WITH e
        MATCH (target)
        WHERE target.decision_id=$target OR target.task_id=$target OR target.sha=$target
           OR target.conflict_id=$target OR target.constraint_id=$target
        MERGE (e)-[r:HISTORICALLY_LINKED]->(target)
        SET r.score=$score, r.reason=$reason, r.relationship=$rel
        """
        async with self._driver.session() as s:
            await s.run(q, eid=source_event_id, target=target_id, score=score, reason=reason, rel=relationship)

    async def find_related_context(self, query: str, limit: int = 6) -> list[dict[str, Any]]:
        q = """
        WITH toLower($query) AS q
        MATCH (n)
        WHERE (n:Decision OR n:Task OR n:Commit OR n:ArchitectureConstraint)
          AND any(term IN split(q, ' ') WHERE size(term) > 3 AND
              toLower(coalesce(n.text, n.title, n.message, '')) CONTAINS term)
        RETURN coalesce(n.decision_id, n.task_id, n.sha, n.constraint_id) AS id,
               labels(n)[0] AS kind,
               coalesce(n.text, n.title, n.message, '') AS summary,
               0.62 AS score
        LIMIT $limit
        """
        async with self._driver.session() as s:
            result = await s.run(q, query=query, limit=limit)
            return await result.data()

    async def reconstruct_causal_chain(self, correlation_id: str) -> list[dict[str, Any]]:
        q = """
        MATCH (te:TimelineEvent {correlation_id:$cid})
        OPTIONAL MATCH path=(te)-[:HISTORICALLY_LINKED|VIOLATES|CAUSED_BY|RECOMMENDED_FIX*1..4]-(n)
        RETURN te.timeline_id AS timeline_id, te.kind AS kind, te.summary AS summary,
               te.timestamp AS timestamp, count(path) AS relationship_count
        ORDER BY te.timestamp ASC
        """
        async with self._driver.session() as s:
            result = await s.run(q, cid=correlation_id)
            return await result.data()

    async def shortest_path_between(self, left_id: str, right_id: str) -> list[dict[str, Any]]:
        q = """
        MATCH (a), (b)
        WHERE any(v IN [a.decision_id, a.task_id, a.sha, a.conflict_id, a.timeline_id] WHERE v=$left)
          AND any(v IN [b.decision_id, b.task_id, b.sha, b.conflict_id, b.timeline_id] WHERE v=$right)
        MATCH p=shortestPath((a)-[*..6]-(b))
        RETURN [n IN nodes(p) | {labels: labels(n), id: coalesce(n.decision_id,n.task_id,n.sha,n.conflict_id,n.timeline_id)}] AS nodes
        LIMIT 1
        """
        async with self._driver.session() as s:
            result = await s.run(q, left=left_id, right=right_id)
            return await result.data()

    async def create_conflict(self, conflict_id: str, conflict_type: str, severity: str,
                              message: str, decision_id: str | None = None) -> None:
        q = """
        MERGE (cf:Conflict {conflict_id: $cid})
        ON CREATE SET cf.type=$ctype, cf.severity=$sev, cf.message=$msg, cf.created_at=datetime()
        """
        async with self._driver.session() as s:
            await s.run(q, cid=conflict_id, ctype=conflict_type, sev=severity, msg=message)
        if decision_id:
            lq = "MATCH (d:Decision {decision_id:$did}),(cf:Conflict {conflict_id:$cid}) MERGE (d)-[:CONFLICTS_WITH]->(cf)"
            async with self._driver.session() as s:
                await s.run(lq, did=decision_id, cid=conflict_id)

    async def get_all_decisions(self) -> list[dict[str, Any]]:
        q = """MATCH (p:Person)-[:MADE_DECISION]->(d:Decision)
        RETURN d.decision_id AS id, d.text AS decision, d.constraint AS constraint,
               d.category AS category, d.importance AS importance, p.name AS made_by
        ORDER BY d.created_at DESC"""
        async with self._driver.session() as s:
            result = await s.run(q)
            return await result.data()

    async def get_decision_constraints(self) -> list[dict[str, Any]]:
        q = """MATCH (d:Decision) WHERE d.constraint IS NOT NULL AND d.constraint <> ''
        RETURN d.decision_id AS id, d.text AS decision, d.constraint AS constraint, d.category AS category"""
        async with self._driver.session() as s:
            result = await s.run(q)
            return await result.data()

    async def get_graph_stats(self) -> dict[str, int]:
        q = """CALL {
            MATCH (p:Person) RETURN 'persons' AS label, count(p) AS cnt UNION ALL
            MATCH (d:Decision) RETURN 'decisions' AS label, count(d) AS cnt UNION ALL
            MATCH (t:Task) RETURN 'tasks' AS label, count(t) AS cnt UNION ALL
            MATCH (c:Commit) RETURN 'commits' AS label, count(c) AS cnt UNION ALL
            MATCH (cf:Conflict) RETURN 'conflicts' AS label, count(cf) AS cnt
            UNION ALL MATCH (i:Incident) RETURN 'incidents' AS label, count(i) AS cnt
            UNION ALL MATCH (r:Recommendation) RETURN 'recommendations' AS label, count(r) AS cnt
            UNION ALL MATCH (ac:ArchitectureConstraint) RETURN 'architecture_constraints' AS label, count(ac) AS cnt
            UNION ALL MATCH (te:TimelineEvent) RETURN 'timeline_events' AS label, count(te) AS cnt
        } RETURN label, cnt"""
        async with self._driver.session() as s:
            result = await s.run(q)
            records = await result.data()
        return {r["label"]: r["cnt"] for r in records}
