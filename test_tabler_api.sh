#!/bin/bash
# CogniWatch Tabler UI API Test Script
# Tests all new endpoints after integration

BASE_URL="http://localhost:9000"
COOKIES="cookies.txt"

echo "🧪 CogniWatch Tabler Integration - API Test Suite"
echo "=================================================="
echo ""

# Step 1: Login
echo "📝 Step 1: Authenticate..."
curl -s -X POST "${BASE_URL}/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}' \
  -c ${COOKIES} | jq -r '.success // empty' > /dev/null 2>&1

if [ $? -eq 0 ]; then
    echo "✅ Login successful"
else
    echo "⚠️  Login failed (may need to set COGNIWATCH_ADMIN_USER/PASSWORD)"
fi
echo ""

# Step 2: Test /api/agents (from detection_results)
echo "🤖 Step 2: Test /api/agents (detection_results table)..."
curl -s "${BASE_URL}/api/agents" -b ${COOKIES} | jq '{
  total: (.total // 0),
  scan_status: .scan_status,
  sample_agent: (.agents[0] // null)
}'
echo ""

# Step 3: Test /api/dashboard/stats
echo "📊 Step 3: Test /api/dashboard/stats (widget data)..."
curl -s "${BASE_URL}/api/dashboard/stats" -b ${COOKIES} | jq '{
  total_agents: .total_agents,
  recent_detections_count: (.recent_detections | length),
  scan_status: .scan_status
}'
echo ""

# Step 4: Test /api/scan/start
echo "🔍 Step 4: Test /api/scan/start..."
SCAN_RESPONSE=$(curl -s -X POST "${BASE_URL}/api/scan/start" -b ${COOKIES})
echo $SCAN_RESPONSE | jq '{
  success: .success,
  scan_id: .scan_id,
  message: .message
}'

SCAN_ID=$(echo $SCAN_RESPONSE | jq -r '.scan_id // empty')
echo ""

# Step 5: Test /api/scan/status
echo "📈 Step 5: Test /api/scan/status..."
sleep 2
curl -s "${BASE_URL}/api/scan/status" -b ${COOKIES} | jq '{
  running: .running,
  progress: .progress,
  hosts_scanned: .hosts_scanned,
  total_hosts: .total_hosts,
  status: .status,
  agents_found: .agents_found
}'
echo ""

# Step 6: Test /api/agents/search
echo "🔎 Step 6: Test /api/agents/search..."
curl -s "${BASE_URL}/api/agents/search?q=openclaw" -b ${COOKIES} | jq '{
  query: .query,
  agents_found: (.agents | length)
}'
echo ""

# Step 7: Test /api/analytics/summary
echo "📉 Step 7: Test /api/analytics/summary..."
curl -s "${BASE_URL}/api/analytics/summary" -b ${COOKIES} | jq '{
  total_agents: .total_agents,
  online_agents: .online_agents,
  recent_detections: .recent_detections
}'
echo ""

# Step 8: Test /api/analytics/frameworks
echo "🏗️  Step 8: Test /api/analytics/frameworks..."
curl -s "${BASE_URL}/api/analytics/frameworks" -b ${COOKIES} | jq '{
  frameworks: .frameworks
}'
echo ""

# Step 9: Test Tabler UI routes
echo "🎨 Step 9: Test Tabler UI page routes..."
for route in dashboard scan agents analytics faq about help; do
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "${BASE_URL}/${route}" -b ${COOKIES})
    if [ "$HTTP_CODE" == "200" ]; then
        echo "  ✅ /${route} - HTTP ${HTTP_CODE}"
    else
        echo "  ⚠️  /${route} - HTTP ${HTTP_CODE}"
    fi
done
echo ""

# Cleanup
rm -f ${COOKIES}

echo "=================================================="
echo "✅ Test suite complete!"
echo ""
echo "📄 Full integration details: /home/neo/cogniwatch/TABLER_INTEGRATION_SUMMARY.md"
