// ============================================
// Nexus-Graph Gateway — Request Logger Middleware
// ============================================

const logger = require("../utils/logger");

/**
 * Express middleware that logs every incoming request
 * with method, URL, status, and response time.
 */
function requestLogger(req, res, next) {
  const start = Date.now();

  // Capture the original end to hook into response completion
  const originalEnd = res.end;
  res.end = function (...args) {
    const duration = Date.now() - start;
    logger.info(`${req.method} ${req.originalUrl} → ${res.statusCode}`, {
      duration_ms: duration,
      ip: req.ip,
      content_length: res.get("Content-Length") || 0,
    });
    originalEnd.apply(res, args);
  };

  next();
}

module.exports = { requestLogger };
