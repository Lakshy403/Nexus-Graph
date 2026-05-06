// ============================================
// Nexus-Graph Gateway — Structured Logger
// ============================================
// Lightweight structured logger with ISO timestamps,
// log levels, and coloured terminal output.
// ============================================

const COLORS = {
  reset: "\x1b[0m",
  dim: "\x1b[2m",
  red: "\x1b[31m",
  green: "\x1b[32m",
  yellow: "\x1b[33m",
  blue: "\x1b[34m",
  magenta: "\x1b[35m",
  cyan: "\x1b[36m",
};

const LEVEL_CONFIG = {
  debug: { label: "DEBUG", color: COLORS.dim },
  info: { label: "INFO ", color: COLORS.green },
  warn: { label: "WARN ", color: COLORS.yellow },
  error: { label: "ERROR", color: COLORS.red },
  event: { label: "EVENT", color: COLORS.cyan },
  graph: { label: "GRAPH", color: COLORS.magenta },
  ai: { label: "AI   ", color: COLORS.blue },
};

function formatMessage(level, message, meta = {}) {
  const ts = new Date().toISOString();
  const cfg = LEVEL_CONFIG[level] || LEVEL_CONFIG.info;
  const metaStr = Object.keys(meta).length
    ? ` ${COLORS.dim}${JSON.stringify(meta)}${COLORS.reset}`
    : "";
  return `${COLORS.dim}[${ts}]${COLORS.reset} ${cfg.color}${cfg.label}${COLORS.reset} ${message}${metaStr}`;
}

const logger = {
  debug: (msg, meta) => console.debug(formatMessage("debug", msg, meta)),
  info: (msg, meta) => console.log(formatMessage("info", msg, meta)),
  warn: (msg, meta) => console.warn(formatMessage("warn", msg, meta)),
  error: (msg, meta) => console.error(formatMessage("error", msg, meta)),
  event: (msg, meta) => console.log(formatMessage("event", msg, meta)),
  graph: (msg, meta) => console.log(formatMessage("graph", msg, meta)),
  ai: (msg, meta) => console.log(formatMessage("ai", msg, meta)),
};

module.exports = logger;
