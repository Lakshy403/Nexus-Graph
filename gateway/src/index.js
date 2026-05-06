// ============================================
// Nexus-Graph Gateway — Main Entry Point
// ============================================
// Bootstraps Express, Socket.io, Redis, and MongoDB,
// then starts listening for incoming events.
// ============================================

const express = require("express");
const http = require("http");
const { Server } = require("socket.io");
const cors = require("cors");

const config = require("./config");
const { connectRedis, disconnectRedis } = require("./config/redis");
const { connectMongoDB, disconnectMongoDB } = require("./config/mongodb");
const { requestLogger } = require("./middleware/logger");
const { initSocketManager } = require("./services/socketManager");
const eventRoutes = require("./routes/events");
const healthRoutes = require("./routes/health");
const logger = require("./utils/logger");

// ---- Express App ----
const app = express();
const server = http.createServer(app);

// ---- Socket.io ----
const io = new Server(server, {
  cors: {
    origin: "*",
    methods: ["GET", "POST"],
  },
  pingTimeout: 60000,
  pingInterval: 25000,
});

// ---- Middleware ----
app.use(cors());
app.use(express.json({ limit: "5mb" }));
app.use(requestLogger);

// ---- Routes ----
app.use("/events", eventRoutes);
app.use("/health", healthRoutes);

// Root
app.get("/", (req, res) => {
  res.json({
    service: "Nexus-Graph AI Gateway",
    version: "1.0.0",
    phase: 1,
    endpoints: {
      events: {
        slack: "POST /events/slack",
        github: "POST /events/github",
        jira: "POST /events/jira",
        batch: "POST /events/batch",
        stats: "GET /events/stats",
      },
      health: "GET /health",
      websocket: "ws://localhost:3000",
    },
  });
});

// 404
app.use((req, res) => {
  res.status(404).json({ error: "Not found" });
});

// Error handler
app.use((err, req, res, _next) => {
  logger.error("Unhandled error", { error: err.message, stack: err.stack });
  res.status(500).json({ error: "Internal server error" });
});

// ---- Bootstrap ----
async function start() {
  try {
    logger.info("🚀 Starting Nexus-Graph Gateway...");
    logger.info(`   Environment : ${config.nodeEnv}`);
    logger.info(`   Port        : ${config.port}`);

    // Connect to infrastructure
    await connectRedis();
    await connectMongoDB();

    // Initialise Socket.io ↔ Redis bridge
    initSocketManager(io);

    // Start HTTP server
    server.listen(config.port, () => {
      logger.info(`✅ Gateway listening on http://0.0.0.0:${config.port}`);
      logger.info("   Channels: " + Object.values(config.channels).join(", "));
    });
  } catch (err) {
    logger.error("❌ Gateway failed to start", { error: err.message });
    process.exit(1);
  }
}

// ---- Graceful shutdown ----
async function shutdown(signal) {
  logger.info(`Received ${signal}. Shutting down gracefully...`);
  server.close();
  await disconnectRedis();
  await disconnectMongoDB();
  process.exit(0);
}

process.on("SIGTERM", () => shutdown("SIGTERM"));
process.on("SIGINT", () => shutdown("SIGINT"));

// ---- Go! ----
start();
