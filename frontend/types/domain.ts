export type Severity = "low" | "medium" | "high" | "critical";

export type GraphNodeKind =
  | "Person"
  | "Decision"
  | "Task"
  | "Commit"
  | "Conflict"
  | "Incident"
  | "ArchitectureConstraint"
  | "Recommendation";

export interface MetricPoint {
  time: string;
  latency: number;
  retrieval: number;
  conflict: number;
  throughput: number;
}

export interface Decision {
  id: string;
  decision: string;
  constraint?: string;
  category: string;
  importance: Severity | "medium";
  made_by?: string;
  timestamp?: string;
  confidence?: number;
  context?: string[];
}

export interface Conflict {
  conflict_id: string;
  type: string;
  severity: Severity;
  confidence: number;
  reasoning: string;
  recommendation: string;
  related_decision_id?: string;
  affected_systems?: string[];
  timestamp?: string;
}

export interface Recommendation {
  recommendation_id: string;
  title: string;
  summary: string;
  action: string;
  priority: string;
  timestamp?: string;
}

export interface TimelineEvent {
  timeline_id: string;
  event_id: string;
  correlation_id: string;
  kind: string;
  summary: string;
  timestamp: string;
  source?: string;
  severity?: Severity;
}

export interface ActivityEvent {
  id: string;
  type: string;
  title: string;
  detail: string;
  timestamp: string;
  severity?: Severity;
}

export interface KnowledgeNode {
  id: string;
  kind: GraphNodeKind;
  label: string;
  subtitle?: string;
  severity?: Severity;
  metadata: Record<string, unknown>;
}

export interface KnowledgeEdge {
  id: string;
  source: string;
  target: string;
  type: "MADE_DECISION" | "LINKED_TO" | "IMPLEMENTED_BY" | "VIOLATES" | "CAUSED_BY" | "RELATED_TO" | "RECOMMENDED_FIX" | "HISTORICALLY_LINKED";
  score?: number;
  animated?: boolean;
}

export interface SystemStats {
  decisions: number;
  conflicts: number;
  semanticHits: number;
  graphRelationships: number;
  throughput: number;
  latency: number;
  activeConnections: number;
}
