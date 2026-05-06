# ============================================
# Nexus-Graph AI — PowerShell Test Script
# ============================================
# Sends mock events to the gateway and queries
# the AI service. Run after docker-compose up.
# ============================================

$Gateway = "http://localhost:3000"
$AIService = "http://localhost:8001"

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  Nexus-Graph AI — Integration Test" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

# ---- Wait for services ----
Write-Host "Waiting for gateway..." -ForegroundColor Yellow
do { Start-Sleep -Seconds 2 } until (
    try { (Invoke-WebRequest -Uri "$Gateway/health" -UseBasicParsing -TimeoutSec 2).StatusCode -eq 200 } catch { $false }
)
Write-Host "Gateway is up" -ForegroundColor Green

Write-Host "Waiting for AI service..." -ForegroundColor Yellow
do { Start-Sleep -Seconds 2 } until (
    try { (Invoke-WebRequest -Uri "$AIService/health" -UseBasicParsing -TimeoutSec 2).StatusCode -eq 200 } catch { $false }
)
Write-Host "AI Service is up" -ForegroundColor Green
Write-Host ""

# ---- Send Slack event ----
Write-Host "Sending Slack event (decision: cooling limit)..." -ForegroundColor Magenta
$slackBody = @{
    type = "slack_message"
    payload = @{
        user = "Backend Lead"
        message = "Keep server cooling at 180C max. This is a hard constraint for all production environments."
        channel = "#infrastructure"
    }
} | ConvertTo-Json -Depth 5
Invoke-RestMethod -Uri "$Gateway/events/slack" -Method POST -ContentType "application/json" -Body $slackBody | ConvertTo-Json
Start-Sleep -Seconds 3

# ---- Send another Slack event ----
Write-Host "Sending Slack event (decision: OAuth2 migration)..." -ForegroundColor Magenta
$slack2 = @{
    type = "slack_message"
    payload = @{
        user = "CTO"
        message = "We are migrating the auth service to OAuth2 by end of Q2. No new basic-auth implementations allowed."
        channel = "#engineering"
    }
} | ConvertTo-Json -Depth 5
Invoke-RestMethod -Uri "$Gateway/events/slack" -Method POST -ContentType "application/json" -Body $slack2 | ConvertTo-Json
Start-Sleep -Seconds 3

# ---- Send GitHub event (should trigger conflict) ----
Write-Host "Sending GitHub commit (potential conflict: TEMP_LIMIT=200)..." -ForegroundColor Magenta
$githubBody = @{
    type = "github_commit"
    payload = @{
        user = "dev-alice"
        repo = "nexus-infra"
        branch = "feature/cooling-update"
        commit_sha = "a1b2c3d4e5f6"
        message = "Update TEMP_LIMIT to 200 in cooling config"
        diff = "- TEMP_LIMIT = 180\n+ TEMP_LIMIT = 200"
    }
} | ConvertTo-Json -Depth 5
Invoke-RestMethod -Uri "$Gateway/events/github" -Method POST -ContentType "application/json" -Body $githubBody | ConvertTo-Json
Start-Sleep -Seconds 3

# ---- Send Jira event ----
Write-Host "Sending Jira ticket..." -ForegroundColor Magenta
$jiraBody = @{
    type = "jira_ticket"
    payload = @{
        user = "Project Manager"
        ticket_id = "NEXUS-101"
        title = "Migrate auth service to OAuth2"
        description = "Complete migration of authentication service from basic auth to OAuth2."
        status = "In Progress"
        priority = "High"
    }
} | ConvertTo-Json -Depth 5
Invoke-RestMethod -Uri "$Gateway/events/jira" -Method POST -ContentType "application/json" -Body $jiraBody | ConvertTo-Json
Start-Sleep -Seconds 5

# ---- Query Results ----
Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  Results" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "Gateway stats:" -ForegroundColor Yellow
Invoke-RestMethod -Uri "$Gateway/events/stats" | ConvertTo-Json

Write-Host "AI Service stats:" -ForegroundColor Yellow
Invoke-RestMethod -Uri "$AIService/stats" | ConvertTo-Json

Write-Host "Extracted decisions:" -ForegroundColor Yellow
Invoke-RestMethod -Uri "$AIService/decisions" | ConvertTo-Json -Depth 5

Write-Host "Semantic search for 'temperature limits':" -ForegroundColor Yellow
$searchBody = @{ query = "temperature limits"; n_results = 3 } | ConvertTo-Json
Invoke-RestMethod -Uri "$AIService/search" -Method POST -ContentType "application/json" -Body $searchBody | ConvertTo-Json -Depth 5

Write-Host "Integration test complete"
