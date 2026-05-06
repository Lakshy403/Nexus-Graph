// ============================================
// Nexus-Graph Gateway - AI gRPC Client
// ============================================

const path = require("path");
const grpc = require("@grpc/grpc-js");
const protoLoader = require("@grpc/proto-loader");
const config = require("../config");
const logger = require("../utils/logger");

const protoCandidates = [
  path.resolve(__dirname, "../../shared/proto/nexus.proto"),
  path.resolve(__dirname, "../../../shared/proto/nexus.proto"),
];
const PROTO_PATH = protoCandidates.find((candidate) => require("fs").existsSync(candidate));
if (!PROTO_PATH) {
  throw new Error("Unable to locate shared protobuf at shared/proto/nexus.proto");
}

const packageDefinition = protoLoader.loadSync(PROTO_PATH, {
  keepCase: false,
  longs: String,
  enums: String,
  defaults: true,
  oneofs: true,
});

const nexusProto = grpc.loadPackageDefinition(packageDefinition).nexus.v1;
let client = null;

function getClient() {
  if (!client) {
    client = new nexusProto.NexusIntelligence(
      config.aiGrpc.url,
      grpc.credentials.createInsecure(),
      {
        "grpc.keepalive_time_ms": 30000,
        "grpc.keepalive_timeout_ms": 10000,
      }
    );
  }
  return client;
}

function toGrpcPayload(event) {
  return {
    eventId: event.event_id,
    type: event.type,
    source: event.source,
    timestamp: event.timestamp,
    correlationId: event.correlation_id || event.event_id,
    payloadJson: JSON.stringify(event.payload || {}),
    metadata: Object.fromEntries(
      Object.entries(event.metadata || {}).map(([key, value]) => [key, String(value)])
    ),
  };
}

function callAnalyze(payload, deadline) {
  return new Promise((resolve, reject) => {
    getClient().AnalyzeEvent(payload, { deadline }, (err, result) => {
      if (err) return reject(err);
      resolve(result);
    });
  });
}

async function analyzeEvent(event) {
  const payload = toGrpcPayload(event);
  let lastError = null;

  for (let attempt = 0; attempt <= config.aiGrpc.retries; attempt++) {
    try {
      const deadline = new Date(Date.now() + config.aiGrpc.timeoutMs);
      const result = await callAnalyze(payload, deadline);
      logger.ai?.("AI gRPC analysis complete", {
        event_id: event.event_id,
        status: result.status,
        attempt,
      });
      return result;
    } catch (err) {
      lastError = err;
      logger.warn("AI gRPC analysis failed", {
        event_id: event.event_id,
        attempt,
        code: err.code,
        error: err.message,
      });
      if (attempt < config.aiGrpc.retries) {
        await new Promise((resolve) => setTimeout(resolve, 200 * (attempt + 1)));
      }
    }
  }

  throw lastError;
}

function streamAnalyzeEvent(event, onChunk) {
  const call = getClient().StreamAnalyzeEvent(toGrpcPayload(event));

  call.on("data", (chunk) => onChunk(chunk));
  call.on("error", (err) => {
    logger.warn("AI gRPC stream failed", {
      event_id: event.event_id,
      code: err.code,
      error: err.message,
    });
  });
  call.on("end", () => {
    logger.debug("AI gRPC stream ended", { event_id: event.event_id });
  });

  return call;
}

module.exports = { analyzeEvent, streamAnalyzeEvent };
