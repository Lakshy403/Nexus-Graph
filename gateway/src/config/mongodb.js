// ============================================
// Nexus-Graph Gateway — MongoDB Client
// ============================================

const { MongoClient } = require("mongodb");
const config = require("./index");
const logger = require("../utils/logger");

let client = null;
let db = null;

async function connectMongoDB() {
  try {
    client = new MongoClient(config.mongodb.uri);
    await client.connect();
    db = client.db(config.mongodb.dbName);

    // Verify connectivity
    await db.command({ ping: 1 });
    logger.info("✅ MongoDB connected", { db: config.mongodb.dbName });
    return db;
  } catch (err) {
    logger.error("MongoDB connection failed", { error: err.message });
    throw err;
  }
}

function getDB() {
  if (!db) throw new Error("MongoDB not initialised — call connectMongoDB first");
  return db;
}

/**
 * Insert a raw event document into the raw_events collection.
 */
async function insertRawEvent(event) {
  const collection = getDB().collection("raw_events");
  const result = await collection.insertOne({
    ...event,
    ingested_at: new Date(),
  });
  logger.debug("Raw event persisted", { event_id: event.event_id, insertedId: result.insertedId });
  return result;
}

/**
 * Insert a processing log entry.
 */
async function insertProcessingLog(log) {
  const collection = getDB().collection("processing_logs");
  return collection.insertOne({
    ...log,
    created_at: new Date(),
  });
}

async function disconnectMongoDB() {
  if (client) {
    await client.close();
    logger.info("MongoDB connection closed");
  }
}

module.exports = {
  connectMongoDB,
  getDB,
  insertRawEvent,
  insertProcessingLog,
  disconnectMongoDB,
};
