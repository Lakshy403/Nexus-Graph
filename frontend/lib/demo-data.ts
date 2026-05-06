import type { ActivityEvent, Conflict, Decision, KnowledgeEdge, KnowledgeNode, MetricPoint, Recommendation, SystemStats, TimelineEvent } from "@/types/domain";

const now = Date.now();
const iso = (offsetMinutes: number) => new Date(now + offsetMinutes * 60_000).toISOString();

export const demoStats: SystemStats = {
  decisions: 18,
  conflicts: 3,
  semanticHits: 142,
  graphRelationships: 87,
  throughput: 34,
  latency: 286,
  activeConnections: 7
};

export const demoMetrics: MetricPoint[] = [
  { time: "10:00", latency: 340, retrieval: 88, conflict: 42, throughput: 18 },
  { time: "10:05", latency: 290, retrieval: 72, conflict: 39, throughput: 26 },
  { time: "10:10", latency: 410, retrieval: 96, conflict: 55, throughput: 31 },
  { time: "10:15", latency: 260, retrieval: 64, conflict: 34, throughput: 38 },
  { time: "10:20", latency: 286, retrieval: 68, conflict: 36, throughput: 34 }
];

export const demoDecisions: Decision[] = [
  {
    id: "dec-cooling-180",
    decision: "Server cooling must remain at 180C max in production.",
    constraint: "Max temperature = 180C",
    category: "Infrastructure",
    importance: "high",
    made_by: "Backend Lead",
    timestamp: iso(-52),
    confidence: 0.91,
    context: ["Slack #infrastructure", "NEXUS-103", "cooling-policy.md"]
  },
  {
    id: "dec-oauth-24",
    decision: "OAuth tokens expire in 24 hours for production APIs.",
    constraint: "TOKEN_EXPIRY_HOURS <= 24",
    category: "Security",
    importance: "critical",
    made_by: "Security Lead",
    timestamp: iso(-34),
    confidence: 0.94,
    context: ["Slack #security", "NEXUS-240", "auth-service"]
  },
  {
    id: "dec-k8s",
    decision: "All new services use Kubernetes deployment manifests.",
    constraint: "Docker Swarm deprecated",
    category: "DevOps",
    importance: "medium",
    made_by: "DevOps Engineer",
    timestamp: iso(-78),
    confidence: 0.87,
    context: ["Slack #devops", "NEXUS-102"]
  }
];

export const demoConflicts: Conflict[] = [
  {
    conflict_id: "conf-token-72",
    type: "security_conflict",
    severity: "critical",
    confidence: 0.94,
    reasoning: "Implementation sets TOKEN_EXPIRY_HOURS to 72, violating the approved 24 hour OAuth token policy.",
    recommendation: "Restore token expiry to 24 hours or request an explicit security exception.",
    related_decision_id: "dec-oauth-24",
    affected_systems: ["auth-service", "feature/session-config", "NEXUS-240"],
    timestamp: iso(-4)
  },
  {
    conflict_id: "conf-temp-200",
    type: "infrastructure_conflict",
    severity: "high",
    confidence: 0.9,
    reasoning: "Commit changes TEMP_LIMIT to 200 while historical infrastructure decision caps cooling at 180C.",
    recommendation: "Block merge and align cooling config with the stored infrastructure constraint.",
    related_decision_id: "dec-cooling-180",
    affected_systems: ["nexus-infra", "cooling config"],
    timestamp: iso(-18)
  },
  {
    conflict_id: "conf-basic-auth",
    type: "policy_violation",
    severity: "high",
    confidence: 0.86,
    reasoning: "New basic-auth middleware conflicts with the OAuth2 migration decision.",
    recommendation: "Replace legacy middleware with OAuth2 compatible authentication.",
    related_decision_id: "dec-oauth-24",
    affected_systems: ["auth-service", "legacy API"],
    timestamp: iso(-27)
  }
];

export const demoRecommendations: Recommendation[] = [
  {
    recommendation_id: "rec-token",
    title: "Review conflicting implementation",
    summary: "Restore OAuth token expiry to 24 hours and add a regression guard.",
    action: "Open remediation task and block merge until Security Lead approval.",
    priority: "urgent",
    timestamp: iso(-3)
  },
  {
    recommendation_id: "rec-cooling",
    title: "Align infrastructure config",
    summary: "Revert TEMP_LIMIT to 180C and link config ownership to NEXUS-103.",
    action: "Create ownership check in CI for cooling policy drift.",
    priority: "high",
    timestamp: iso(-14)
  }
];

export const demoTimeline: TimelineEvent[] = [
  { timeline_id: "tl-1", event_id: "evt-slack-auth", correlation_id: "corr-auth-token-policy", kind: "slack_discussion", summary: "Security Lead defines OAuth token expiry policy.", timestamp: iso(-34), source: "slack" },
  { timeline_id: "tl-2", event_id: "evt-decision-auth", correlation_id: "corr-auth-token-policy", kind: "architecture_decision", summary: "Decision stored: OAuth tokens expire in 24 hours.", timestamp: iso(-33), source: "ai-service" },
  { timeline_id: "tl-3", event_id: "evt-jira-auth", correlation_id: "corr-auth-token-policy", kind: "jira_task", summary: "NEXUS-240 tracks policy implementation.", timestamp: iso(-25), source: "jira" },
  { timeline_id: "tl-4", event_id: "evt-commit-auth", correlation_id: "corr-auth-token-policy", kind: "github_commit", summary: "Commit changes TOKEN_EXPIRY_HOURS from 24 to 72.", timestamp: iso(-5), source: "github" },
  { timeline_id: "tl-5", event_id: "evt-conflict-auth", correlation_id: "corr-auth-token-policy", kind: "production_conflict", summary: "Decision drift detected against security policy.", timestamp: iso(-4), source: "ai-service", severity: "critical" },
  { timeline_id: "tl-6", event_id: "evt-rec-auth", correlation_id: "corr-auth-token-policy", kind: "ai_recommendation", summary: "Restore 24 hour expiry and request security approval.", timestamp: iso(-3), source: "ai-service" }
];

export const demoNodes: KnowledgeNode[] = [
  { id: "person-security", kind: "Person", label: "Security Lead", subtitle: "Policy owner", metadata: { role: "Security" } },
  { id: "dec-oauth-24", kind: "Decision", label: "OAuth token expiry", subtitle: "24 hour max", severity: "critical", metadata: { ...demoDecisions[1] } },
  { id: "task-nexus-240", kind: "Task", label: "NEXUS-240", subtitle: "Implement token policy", metadata: { status: "In Progress" } },
  { id: "commit-f0e1", kind: "Commit", label: "f0e1d2c", subtitle: "TOKEN_EXPIRY=72", metadata: { repo: "auth-service" } },
  { id: "conf-token-72", kind: "Conflict", label: "Token policy drift", subtitle: "Critical", severity: "critical", metadata: { ...demoConflicts[0] } },
  { id: "incident-auth", kind: "Incident", label: "Auth policy incident", subtitle: "Generated from conflict", severity: "critical", metadata: { caused_by: "conf-token-72" } },
  { id: "rec-token", kind: "Recommendation", label: "Restore expiry", subtitle: "Block merge", metadata: { ...demoRecommendations[0] } },
  { id: "person-backend", kind: "Person", label: "Backend Lead", subtitle: "Infrastructure owner", metadata: { role: "Engineering" } },
  { id: "dec-cooling-180", kind: "Decision", label: "Cooling max 180C", subtitle: "Infrastructure", severity: "high", metadata: { ...demoDecisions[0] } },
  { id: "constraint-cooling", kind: "ArchitectureConstraint", label: "Max temp = 180C", subtitle: "Constraint", severity: "high", metadata: { category: "Infrastructure" } },
  { id: "commit-cooling", kind: "Commit", label: "a1b2c3d", subtitle: "TEMP_LIMIT=200", metadata: { repo: "nexus-infra" } },
  { id: "conf-temp-200", kind: "Conflict", label: "Cooling drift", subtitle: "High", severity: "high", metadata: { ...demoConflicts[1] } }
];

export const demoEdges: KnowledgeEdge[] = [
  { id: "e1", source: "person-security", target: "dec-oauth-24", type: "MADE_DECISION" },
  { id: "e2", source: "dec-oauth-24", target: "task-nexus-240", type: "LINKED_TO" },
  { id: "e3", source: "task-nexus-240", target: "commit-f0e1", type: "IMPLEMENTED_BY", animated: true },
  { id: "e4", source: "commit-f0e1", target: "conf-token-72", type: "VIOLATES", animated: true },
  { id: "e5", source: "incident-auth", target: "conf-token-72", type: "CAUSED_BY" },
  { id: "e6", source: "conf-token-72", target: "rec-token", type: "RECOMMENDED_FIX", animated: true },
  { id: "e7", source: "person-backend", target: "dec-cooling-180", type: "MADE_DECISION" },
  { id: "e8", source: "dec-cooling-180", target: "constraint-cooling", type: "RELATED_TO" },
  { id: "e9", source: "commit-cooling", target: "conf-temp-200", type: "VIOLATES", animated: true },
  { id: "e10", source: "conf-temp-200", target: "dec-cooling-180", type: "HISTORICALLY_LINKED" }
];

export const demoActivity: ActivityEvent[] = [
  { id: "act-1", type: "conflict:detected", title: "Security conflict detected", detail: "TOKEN_EXPIRY_HOURS moved beyond approved policy.", timestamp: iso(-4), severity: "critical" },
  { id: "act-2", type: "graph:update", title: "Graph relationship added", detail: "Commit f0e1d2c VIOLATES decision dec-oauth-24.", timestamp: iso(-4) },
  { id: "act-3", type: "decision:created", title: "Decision indexed", detail: "OAuth token expiry policy stored in semantic memory.", timestamp: iso(-33), severity: "high" }
];
