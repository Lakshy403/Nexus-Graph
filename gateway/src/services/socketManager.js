// ============================================
// Nexus-Graph Gateway — Socket.io Manager
// ============================================
// Manages real-time WebSocket connections.
// Subscribes to Redis channels and broadcasts
// events to connected clients.
// ============================================

const { getSubscriber } = require("../config/redis");
const config = require("../config");
const { SOCKET_EVENT_MAP } = require("../pubsub/channels");
const logger = require("../utils/logger");

let io = null;

function initSocketManager(socketServer) {
  io = socketServer;

  io.on("connection", (socket) => {
    logger.info("🔌 WebSocket client connected", { id: socket.id });

    // Allow clients to join specific event rooms
    socket.on("subscribe", (channel) => {
      if (Object.values(config.channels).includes(channel)) {
        socket.join(channel);
        logger.info(`Client joined room: ${channel}`, { id: socket.id });
        socket.emit("subscribed", { channel, status: "ok" });
      } else {
        socket.emit("error", { message: `Unknown channel: ${channel}` });
      }
    });

    socket.on("unsubscribe", (channel) => {
      socket.leave(channel);
      logger.info(`Client left room: ${channel}`, { id: socket.id });
    });

    socket.on("disconnect", (reason) => {
      logger.info("🔌 WebSocket client disconnected", {
        id: socket.id,
        reason,
      });
    });
  });

  // Subscribe to all Redis channels and broadcast to Socket.io rooms
  const subscriber = getSubscriber();
  const allChannels = Object.values(config.channels);

  allChannels.forEach((channel) => {
    subscriber.subscribe(channel, (err) => {
      if (err) {
        logger.error(`Failed to subscribe to ${channel}`, { error: err.message });
      } else {
        logger.info(`📡 Listening on Redis channel: ${channel}`);
      }
    });
  });

  subscriber.on("message", (channel, message) => {
    try {
      const event = JSON.parse(message);
      const socketEvent = SOCKET_EVENT_MAP[channel] || "event";
      // Broadcast to all clients in the matching Socket.io room
      io.to(channel).emit("event", { channel, data: event });
      io.to(channel).emit(socketEvent, event);
      // Also broadcast to a global "all-events" namespace
      io.emit("all-events", { channel, data: event });
      io.emit(socketEvent, event);
    } catch (err) {
      logger.error("Failed to parse Redis message for Socket.io", {
        channel,
        error: err.message,
      });
    }
  });

  logger.info("✅ Socket.io manager initialised");
}

function getIO() {
  if (!io) throw new Error("Socket.io not initialised");
  return io;
}

module.exports = { initSocketManager, getIO };
