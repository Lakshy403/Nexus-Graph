// ============================================
// Nexus-Graph Gateway — Redis Client
// ============================================
// Two separate ioredis instances:
//   publisher  – used by the gateway to publish events
//   subscriber – used to listen for processed results
// ============================================

const Redis = require("ioredis");
const config = require("./index");
const logger = require("../utils/logger");

let publisher = null;
let subscriber = null;

async function connectRedis() {
  return new Promise((resolve, reject) => {
    publisher = new Redis(config.redis.url, {
      retryStrategy: (times) => Math.min(times * 200, 5000),
      maxRetriesPerRequest: 3,
    });

    subscriber = new Redis(config.redis.url, {
      retryStrategy: (times) => Math.min(times * 200, 5000),
      maxRetriesPerRequest: 3,
    });

    let readyCount = 0;
    const onReady = () => {
      readyCount++;
      if (readyCount === 2) {
        logger.info("✅ Redis publisher & subscriber connected", {
          url: config.redis.url,
        });
        resolve();
      }
    };

    publisher.on("ready", onReady);
    subscriber.on("ready", onReady);

    publisher.on("error", (err) => {
      logger.error("Redis publisher error", { error: err.message });
      if (readyCount < 2) reject(err);
    });

    subscriber.on("error", (err) => {
      logger.error("Redis subscriber error", { error: err.message });
      if (readyCount < 2) reject(err);
    });
  });
}

function getPublisher() {
  if (!publisher) throw new Error("Redis publisher not initialised");
  return publisher;
}

function getSubscriber() {
  if (!subscriber) throw new Error("Redis subscriber not initialised");
  return subscriber;
}

async function disconnectRedis() {
  if (publisher) await publisher.quit();
  if (subscriber) await subscriber.quit();
  logger.info("Redis connections closed");
}

module.exports = { connectRedis, getPublisher, getSubscriber, disconnectRedis };
