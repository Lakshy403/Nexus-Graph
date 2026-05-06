// ============================================
// Nexus-Graph Gateway — Configuration
// ============================================

const config = {
  port: parseInt(process.env.GATEWAY_PORT, 10) || 3000,
  nodeEnv: process.env.NODE_ENV || "development",

  redis: {
    url: process.env.REDIS_URL || "redis://localhost:6379",
  },

  aiGrpc: {
    url: process.env.AI_GRPC_URL || "localhost:50051",
    timeoutMs: parseInt(process.env.AI_GRPC_TIMEOUT_MS, 10) || 12000,
    retries: parseInt(process.env.AI_GRPC_RETRIES, 10) || 2,
  },

  mongodb: {
    uri: process.env.MONGODB_URI || "mongodb://localhost:27017/nexus_graph",
    dbName: "nexus_graph",
  },

  // Pub/Sub channel names
  channels: {
    SLACK_EVENTS: "slack-events",
    GITHUB_EVENTS: "github-events",
    JIRA_EVENTS: "jira-events",
    DECISION_EVENTS: "decision-events",
    CONFLICT_EVENTS: "conflict-events",
    GRAPH_UPDATES: "graph-updates",
    TIMELINE_EVENTS: "timeline-events",
    ORCHESTRATION_EVENTS: "orchestration-events",
  },
};

module.exports = config;
