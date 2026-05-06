const { v4: uuidv4 } = require("uuid");

function buildEventEnvelope({ type, source, payload, timestamp, correlationId, metadata = {} }) {
  const eventId = uuidv4();
  return {
    event_id: eventId,
    correlation_id: correlationId || metadata.correlation_id || eventId,
    type,
    source,
    timestamp: timestamp || new Date().toISOString(),
    payload,
    metadata: {
      processed: false,
      received_at: new Date().toISOString(),
      ...metadata,
    },
  };
}

module.exports = { buildEventEnvelope };
