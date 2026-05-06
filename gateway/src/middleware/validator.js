// ============================================
// Nexus-Graph Gateway — Event Validator Middleware
// ============================================

const logger = require("../utils/logger");

const VALID_EVENT_TYPES = {
  slack: ["slack_message"],
  github: ["github_commit", "github_pr"],
  jira: ["jira_ticket", "jira_comment"],
};

/**
 * Validates incoming event payloads.
 * Returns 400 with details if the payload is malformed.
 */
function validateEvent(source) {
  return (req, res, next) => {
    const body = req.body;
    const errors = [];

    // Must have a type
    if (!body.type) {
      errors.push("Missing required field: type");
    } else if (VALID_EVENT_TYPES[source] && !VALID_EVENT_TYPES[source].includes(body.type)) {
      errors.push(
        `Invalid event type '${body.type}' for source '${source}'. ` +
          `Expected one of: ${VALID_EVENT_TYPES[source].join(", ")}`
      );
    }

    // Must have a payload object
    if (!body.payload || typeof body.payload !== "object") {
      errors.push("Missing or invalid field: payload (must be an object)");
    }

    // Payload must have a user
    if (body.payload && !body.payload.user) {
      errors.push("Missing required field: payload.user");
    }

    if (errors.length > 0) {
      logger.warn("Event validation failed", { source, errors });
      return res.status(400).json({
        success: false,
        errors,
      });
    }

    // Normalise source
    req.body.source = source;
    next();
  };
}

module.exports = { validateEvent };
