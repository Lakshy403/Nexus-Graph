// ============================================
// Nexus-Graph Gateway — Event Routes
// ============================================

const { Router } = require("express");
const { validateEvent } = require("../middleware/validator");
const { publishEvent } = require("../services/eventBus");
const { insertRawEvent, insertProcessingLog } = require("../config/mongodb");
const { buildEventEnvelope } = require("../events/eventEnvelope");
const { SOURCE_CHANNEL_MAP } = require("../pubsub/channels");
const { analyzeEvent } = require("../grpc/aiClient");
const logger = require("../utils/logger");

const router = Router();

/**
 * Generic handler for all event ingestion endpoints.
 * 1. Enriches the event with an ID + timestamp
 * 2. Persists to MongoDB (raw_events)
 * 3. Publishes to the appropriate Redis channel
 * 4. Returns the enriched event to the caller
 */
async function handleEvent(req, res) {
  const start = Date.now();
  const source = req.body.source;

  try {
    // Enrich event
    const event = buildEventEnvelope({
      type: req.body.type,
      source,
      timestamp: req.body.timestamp,
      payload: req.body.payload,
      correlationId: req.body.correlation_id,
      metadata: req.body.metadata,
    });
    event.metadata.ai_route = "grpc_primary";

    // Persist raw event to MongoDB
    await insertRawEvent(event);

    // Publish to Redis channel
    const channel = SOURCE_CHANNEL_MAP[source];
    if (channel) {
      await publishEvent(channel, event);
    }

    // Phase 2: trigger AI analysis through gRPC. Redis still carries the
    // event bus flow, while gRPC gives the gateway a direct orchestration path.
    let analysis = null;
    try {
      analysis = await analyzeEvent(event);
    } catch (err) {
      logger.warn("Continuing after AI gRPC failure", {
        event_id: event.event_id,
        error: err.message,
      });
      if (channel) {
        event.metadata.ai_route = "redis_fallback";
        await publishEvent(channel, event);
      }
    }

    // Log processing
    const duration = Date.now() - start;
    await insertProcessingLog({
      event_id: event.event_id,
      stage: "ingestion",
      status: "success",
      duration_ms: duration,
      source,
    });

    logger.event(`Ingested ${event.type} from ${source}`, {
      event_id: event.event_id,
      duration_ms: duration,
    });

    return res.status(201).json({
      success: true,
      event_id: event.event_id,
      correlation_id: event.correlation_id,
      channel,
      analysis_status: analysis ? analysis.status : "queued_or_unavailable",
      duration_ms: duration,
    });
  } catch (err) {
    const duration = Date.now() - start;
    logger.error(`Event ingestion failed for ${source}`, {
      error: err.message,
      duration_ms: duration,
    });

    return res.status(500).json({
      success: false,
      error: "Internal server error during event ingestion",
    });
  }
}

// ---- REST Endpoints ----

/** POST /events/slack */
router.post("/slack", validateEvent("slack"), handleEvent);

/** POST /events/github */
router.post("/github", validateEvent("github"), handleEvent);

/** POST /events/jira */
router.post("/jira", validateEvent("jira"), handleEvent);

/**
 * POST /events/batch
 * Accept an array of events and process them sequentially.
 */
router.post("/batch", async (req, res) => {
  const events = req.body.events;

  if (!Array.isArray(events) || events.length === 0) {
    return res.status(400).json({
      success: false,
      error: "Request body must contain a non-empty 'events' array",
    });
  }

  const results = [];
  for (const eventData of events) {
    const source = eventData.source;
    const channel = SOURCE_CHANNEL_MAP[source];

    try {
      const event = buildEventEnvelope({
        type: eventData.type,
        source,
        timestamp: eventData.timestamp,
        payload: eventData.payload,
        correlationId: eventData.correlation_id,
        metadata: eventData.metadata,
      });
      event.metadata.ai_route = "grpc_primary";

      await insertRawEvent(event);

      if (channel) {
        await publishEvent(channel, event);
      }

      analyzeEvent(event).catch(async (err) => {
        logger.warn("Batch AI gRPC analysis failed", {
          event_id: event.event_id,
          error: err.message,
        });
        if (channel) {
          event.metadata.ai_route = "redis_fallback";
          await publishEvent(channel, event);
        }
      });

      results.push({ event_id: event.event_id, correlation_id: event.correlation_id, status: "success" });
    } catch (err) {
      results.push({ source, status: "error", error: err.message });
    }
  }

  logger.event(`Batch ingested ${results.length} events`);
  return res.status(201).json({ success: true, results });
});

/**
 * GET /events/stats
 * Quick stats about ingested events.
 */
router.get("/stats", async (req, res) => {
  try {
    const { getDB } = require("../config/mongodb");
    const db = getDB();
    const rawCount = await db.collection("raw_events").countDocuments();
    const decisionCount = await db.collection("extracted_decisions").countDocuments();
    const logCount = await db.collection("processing_logs").countDocuments();

    return res.json({
      raw_events: rawCount,
      extracted_decisions: decisionCount,
      processing_logs: logCount,
    });
  } catch (err) {
    return res.status(500).json({ error: err.message });
  }
});

module.exports = router;
