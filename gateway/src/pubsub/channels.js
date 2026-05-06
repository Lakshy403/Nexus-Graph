const config = require("../config");

const SOURCE_CHANNEL_MAP = {
  slack: config.channels.SLACK_EVENTS,
  github: config.channels.GITHUB_EVENTS,
  jira: config.channels.JIRA_EVENTS,
};

const SOCKET_EVENT_MAP = {
  [config.channels.DECISION_EVENTS]: "decision:created",
  [config.channels.CONFLICT_EVENTS]: "conflict:detected",
  "graph-updates": "graph:update",
  "timeline-events": "timeline:update",
  "orchestration-events": "orchestration:status",
};

module.exports = { SOURCE_CHANNEL_MAP, SOCKET_EVENT_MAP };
