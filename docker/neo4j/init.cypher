// ============================================
// Nexus-Graph — Neo4j Initialization Script
// Run via:  cypher-shell -f init.cypher
// ============================================

// ---- Constraints (uniqueness) ----
CREATE CONSTRAINT person_name IF NOT EXISTS
  FOR (p:Person) REQUIRE p.name IS UNIQUE;

CREATE CONSTRAINT decision_id IF NOT EXISTS
  FOR (d:Decision) REQUIRE d.decision_id IS UNIQUE;

CREATE CONSTRAINT task_id IF NOT EXISTS
  FOR (t:Task) REQUIRE t.task_id IS UNIQUE;

CREATE CONSTRAINT commit_sha IF NOT EXISTS
  FOR (c:Commit) REQUIRE c.sha IS UNIQUE;

CREATE CONSTRAINT conflict_id IF NOT EXISTS
  FOR (cf:Conflict) REQUIRE cf.conflict_id IS UNIQUE;

CREATE CONSTRAINT incident_id IF NOT EXISTS
  FOR (i:Incident) REQUIRE i.incident_id IS UNIQUE;

CREATE CONSTRAINT recommendation_id IF NOT EXISTS
  FOR (r:Recommendation) REQUIRE r.recommendation_id IS UNIQUE;

CREATE CONSTRAINT architecture_constraint_id IF NOT EXISTS
  FOR (ac:ArchitectureConstraint) REQUIRE ac.constraint_id IS UNIQUE;

CREATE CONSTRAINT timeline_event_id IF NOT EXISTS
  FOR (te:TimelineEvent) REQUIRE te.timeline_id IS UNIQUE;

// ---- Indexes for fast lookups ----
CREATE INDEX decision_category IF NOT EXISTS
  FOR (d:Decision) ON (d.category);

CREATE INDEX decision_importance IF NOT EXISTS
  FOR (d:Decision) ON (d.importance);

CREATE INDEX conflict_severity IF NOT EXISTS
  FOR (cf:Conflict) ON (cf.severity);

CREATE INDEX task_status IF NOT EXISTS
  FOR (t:Task) ON (t.status);

CREATE INDEX timeline_correlation IF NOT EXISTS
  FOR (te:TimelineEvent) ON (te.correlation_id);

CREATE INDEX incident_severity IF NOT EXISTS
  FOR (i:Incident) ON (i.severity);

// ---- Seed: sample Person nodes ----
MERGE (p1:Person {name: "Backend Lead"})
  SET p1.role = "Engineering", p1.created_at = datetime();

MERGE (p2:Person {name: "CTO"})
  SET p2.role = "Executive", p2.created_at = datetime();

MERGE (p3:Person {name: "DevOps Engineer"})
  SET p3.role = "Operations", p3.created_at = datetime();

MERGE (p4:Person {name: "Security Lead"})
  SET p4.role = "Security", p4.created_at = datetime();

MERGE (p5:Person {name: "Frontend Lead"})
  SET p5.role = "Engineering", p5.created_at = datetime();

RETURN "Neo4j initialized for Nexus-Graph AI" AS status;
