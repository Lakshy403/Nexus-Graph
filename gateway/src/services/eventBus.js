// ============================================
// Nexus-Graph Gateway — Event Bus (Redis Pub/Sub)
// ============================================

const { getPublisher } = require("../config/redis");
const logger = require("../utils/logger");

/**
 * Publish an event to a specific Redis Pub/Sub channel.
 * @param {string} channel - The channel name (e.g. "slack-events")
 * @param {object} event   - The event payload to publish
 */
async function publishEvent(channel, event) {
  const publisher = getPublisher();
  const message = JSON.stringify(event);

  await publisher.publish(channel, message);

  logger.event(`Published to [${channel}]`, {
    event_id: event.event_id,
    type: event.type,
  });
}

/**
 * Publish to multiple channels simultaneously.
 * Useful when an event should fan out (e.g. raw + decision channels).
 */
async function publishToMultiple(channels, event) {
  const publisher = getPublisher();
  const message = JSON.stringify(event);

  const promises = channels.map((ch) => publisher.publish(ch, message));
  await Promise.all(promises);

  logger.event(`Published to ${channels.length} channels`, {
    channels,
    event_id: event.event_id,
  });
}

module.exports = { publishEvent, publishToMultiple };
