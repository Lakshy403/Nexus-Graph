// ============================================
// Nexus-Graph Gateway — Health Routes
// ============================================

const { Router } = require("express");
const { getPublisher } = require("../config/redis");
const { getDB } = require("../config/mongodb");

const router = Router();

/**
 * GET /health
 * Comprehensive health check for the gateway and its dependencies.
 */
router.get("/", async (req, res) => {
  const checks = {};
  let allHealthy = true;

  // Gateway
  checks.gateway = { status: "healthy", uptime_s: Math.floor(process.uptime()) };

  // Redis
  try {
    const redis = getPublisher();
    const pong = await redis.ping();
    checks.redis = { status: pong === "PONG" ? "healthy" : "degraded" };
  } catch (err) {
    checks.redis = { status: "unhealthy", error: err.message };
    allHealthy = false;
  }

  // MongoDB
  try {
    const db = getDB();
    await db.command({ ping: 1 });
    checks.mongodb = { status: "healthy" };
  } catch (err) {
    checks.mongodb = { status: "unhealthy", error: err.message };
    allHealthy = false;
  }

  const statusCode = allHealthy ? 200 : 503;
  return res.status(statusCode).json({
    service: "nexus-graph-gateway",
    status: allHealthy ? "healthy" : "degraded",
    timestamp: new Date().toISOString(),
    checks,
  });
});

module.exports = router;
