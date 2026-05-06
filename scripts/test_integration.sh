#!/usr/bin/env bash
# ============================================
# Nexus-Graph AI — Test Script
# ============================================
# Sends mock events to the gateway and queries
# the AI service. Run after docker-compose up.
# ============================================

set -e

GATEWAY="http://localhost:3000"
AI_SERVICE="http://localhost:8001"

echo "============================================"
echo "  Nexus-Graph AI — Integration Test"
echo "============================================"
echo ""

# ---- Wait for services ----
echo "⏳ Waiting for gateway..."
until curl -s "$GATEWAY/health" > /dev/null 2>&1; do sleep 2; done
echo "✅ Gateway is up"

echo "⏳ Waiting for AI service..."
until curl -s "$AI_SERVICE/health" > /dev/null 2>&1; do sleep 2; done
echo "✅ AI Service is up"
echo ""

# ---- Send Slack events ----
echo "📨 Sending Slack event (decision: cooling limit)..."
curl -s -X POST "$GATEWAY/events/slack" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "slack_message",
    "payload": {
      "user": "Backend Lead",
      "message": "Keep server cooling at 180°C max. This is a hard constraint for all production environments.",
      "channel": "#infrastructure"
    }
  }' | python3 -m json.tool
echo ""

sleep 3

echo "📨 Sending Slack event (decision: OAuth2 migration)..."
curl -s -X POST "$GATEWAY/events/slack" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "slack_message",
    "payload": {
      "user": "CTO",
      "message": "We are migrating the auth service to OAuth2 by end of Q2. No new basic-auth implementations allowed.",
      "channel": "#engineering"
    }
  }' | python3 -m json.tool
echo ""

sleep 3

# ---- Send GitHub event (should trigger conflict) ----
echo "📨 Sending GitHub commit (potential conflict: TEMP_LIMIT=200)..."
curl -s -X POST "$GATEWAY/events/github" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "github_commit",
    "payload": {
      "user": "dev-alice",
      "repo": "nexus-infra",
      "branch": "feature/cooling-update",
      "commit_sha": "a1b2c3d4e5f6",
      "message": "Update TEMP_LIMIT to 200 in cooling config",
      "diff": "- TEMP_LIMIT = 180\n+ TEMP_LIMIT = 200"
    }
  }' | python3 -m json.tool
echo ""

sleep 3

# ---- Send Jira event ----
echo "📨 Sending Jira ticket..."
curl -s -X POST "$GATEWAY/events/jira" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "jira_ticket",
    "payload": {
      "user": "Project Manager",
      "ticket_id": "NEXUS-101",
      "title": "Migrate auth service to OAuth2",
      "description": "Complete migration of authentication service from basic auth to OAuth2.",
      "status": "In Progress",
      "priority": "High"
    }
  }' | python3 -m json.tool
echo ""

sleep 5

# ---- Query results ----
echo "============================================"
echo "  📊 Results"
echo "============================================"
echo ""

echo "📈 Gateway stats:"
curl -s "$GATEWAY/events/stats" | python3 -m json.tool
echo ""

echo "📈 AI Service stats:"
curl -s "$AI_SERVICE/stats" | python3 -m json.tool
echo ""

echo "🧠 Extracted decisions:"
curl -s "$AI_SERVICE/decisions" | python3 -m json.tool
echo ""

echo "🔍 Semantic search for 'temperature limits':"
curl -s -X POST "$AI_SERVICE/search" \
  -H "Content-Type: application/json" \
  -d '{"query": "temperature limits", "n_results": 3}' | python3 -m json.tool
echo ""

echo "✅ Integration test complete!"
