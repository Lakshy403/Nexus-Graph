// ============================================
// Nexus-Graph — MongoDB Initialization Script
// Runs automatically on first container start
// ============================================

db = db.getSiblingDB("nexus_graph");

// ---- Collections ----
db.createCollection("raw_events");
db.createCollection("extracted_decisions");
db.createCollection("processing_logs");
db.createCollection("generated_issues");
db.createCollection("timeline_events");

// ---- Indexes: raw_events ----
db.raw_events.createIndex({ event_id: 1 }, { unique: true });
db.raw_events.createIndex({ type: 1 });
db.raw_events.createIndex({ "payload.user": 1 });
db.raw_events.createIndex({ timestamp: -1 });
db.raw_events.createIndex({ source: 1, timestamp: -1 });

// ---- Indexes: extracted_decisions ----
db.extracted_decisions.createIndex({ event_id: 1 });
db.extracted_decisions.createIndex({ category: 1 });
db.extracted_decisions.createIndex({ importance: 1 });
db.extracted_decisions.createIndex({ created_at: -1 });
db.extracted_decisions.createIndex(
  { decision: "text", constraint: "text" },
  { name: "decision_text_search" }
);

// ---- Indexes: processing_logs ----
db.processing_logs.createIndex({ event_id: 1 });
db.processing_logs.createIndex({ status: 1 });
db.processing_logs.createIndex({ created_at: -1 });

// ---- Indexes: generated_issues ----
db.generated_issues.createIndex({ issue_id: 1 }, { unique: true });
db.generated_issues.createIndex({ source_event_id: 1 });
db.generated_issues.createIndex({ correlation_id: 1 });
db.generated_issues.createIndex({ severity: 1 });
db.generated_issues.createIndex({ created_at: -1 });

// ---- Indexes: timeline_events ----
db.timeline_events.createIndex({ timeline_id: 1 }, { unique: true });
db.timeline_events.createIndex({ event_id: 1 });
db.timeline_events.createIndex({ correlation_id: 1, timestamp: 1 });
db.timeline_events.createIndex({ kind: 1 });

print("MongoDB initialized for Nexus-Graph AI");
