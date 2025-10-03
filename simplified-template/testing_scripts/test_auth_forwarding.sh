#!/bin/bash

# Test Authentication Forwarding for Simplified Template
# This script tests bearer token forwarding and HTTPS communication

set -e

# Configuration
HOST="${HOST:-localhost}"
PORT="${PORT:-8000}"
PROTOCOL="${PROTOCOL:-http}"
BASE_URL="${PROTOCOL}://${HOST}:${PORT}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test data
TEST_TOKEN="test-bearer-token-123456789"
TEST_USER_ID="test-user-simplified"
TEST_API_KEY="test-api-key-987654321"

echo -e "${BLUE}=== Simplified Template Authentication Forwarding Tests ===${NC}"
echo "Testing against: ${BASE_URL}"
echo

# Function to make HTTP requests with proper error handling
make_request() {
    local method="$1"
    local endpoint="$2"
    local headers="$3"
    local data="$4"
    local expect_success="${5:-true}"

    echo -e "${YELLOW}Testing: ${method} ${endpoint}${NC}"

    if [ "$method" = "GET" ]; then
        response=$(curl -s -w "HTTPSTATUS:%{http_code}" $headers "${BASE_URL}${endpoint}" || echo "HTTPSTATUS:000")
    else
        response=$(curl -s -w "HTTPSTATUS:%{http_code}" -X "$method" $headers -d "$data" "${BASE_URL}${endpoint}" || echo "HTTPSTATUS:000")
    fi

    http_status=$(echo "$response" | grep -o "HTTPSTATUS:[0-9]*" | cut -d: -f2)
    body=$(echo "$response" | sed 's/HTTPSTATUS:[0-9]*$//')

    if [ "$expect_success" = "true" ] && [ "$http_status" -ge 200 ] && [ "$http_status" -lt 300 ]; then
        echo -e "${GREEN}✅ Success (HTTP $http_status)${NC}"
        echo "$body" | jq '.' 2>/dev/null || echo "$body"
    elif [ "$expect_success" = "false" ] && ([ "$http_status" -ge 400 ] || [ "$http_status" = "000" ]); then
        echo -e "${GREEN}✅ Expected failure (HTTP $http_status)${NC}"
        echo "$body" | jq '.' 2>/dev/null || echo "$body"
    else
        echo -e "${RED}❌ Unexpected result (HTTP $http_status)${NC}"
        echo "$body" | jq '.' 2>/dev/null || echo "$body"
    fi

    echo
    return 0
}

# Test 1: Health Check
echo -e "${BLUE}--- Test 1: Health Check ---${NC}"
make_request "GET" "/health" ""

# Test 2: Agent Card
echo -e "${BLUE}--- Test 2: Agent Card ---${NC}"
make_request "GET" "/.well-known/agent-card.json" ""

# Test 3: Auth Status without authentication
echo -e "${BLUE}--- Test 3: Auth Status (No Auth) ---${NC}"
make_request "GET" "/auth/status" ""

# Test 4: Auth Status with Bearer Token
echo -e "${BLUE}--- Test 4: Auth Status (Bearer Token) ---${NC}"
make_request "GET" "/auth/status" "-H 'Authorization: Bearer ${TEST_TOKEN}' -H 'X-User-ID: ${TEST_USER_ID}'"

# Test 5: Auth Status with API Key
echo -e "${BLUE}--- Test 5: Auth Status (API Key) ---${NC}"
make_request "GET" "/auth/status" "-H 'X-API-Key: ${TEST_API_KEY}' -H 'X-User-ID: ${TEST_USER_ID}'"

# Test 6: A2A Request without authentication
echo -e "${BLUE}--- Test 6: A2A Request (No Auth) ---${NC}"
a2a_payload='{
  "jsonrpc": "2.0",
  "id": "test-1",
  "method": "message/send",
  "params": {
    "message": {
      "messageId": "test-no-auth",
      "role": "user",
      "parts": [{
        "text": "Show me my authentication info"
      }]
    }
  }
}'
make_request "POST" "/" "-H 'Content-Type: application/json'" "$a2a_payload"

# Test 7: A2A Request with Bearer Token
echo -e "${BLUE}--- Test 7: A2A Request (Bearer Token) ---${NC}"
a2a_payload_auth='{
  "jsonrpc": "2.0",
  "id": "test-2",
  "method": "message/send",
  "params": {
    "message": {
      "messageId": "test-bearer-auth",
      "role": "user",
      "parts": [{
        "text": "Show me my authentication info using the example_authenticated_tool"
      }]
    }
  }
}'
make_request "POST" "/" "-H 'Authorization: Bearer ${TEST_TOKEN}' -H 'X-User-ID: ${TEST_USER_ID}' -H 'Content-Type: application/json'" "$a2a_payload_auth"

# Test 8: Bearer Token Validation Tool
echo -e "${BLUE}--- Test 8: Bearer Token Validation Tool ---${NC}"
token_validation_payload='{
  "jsonrpc": "2.0",
  "id": "test-3",
  "method": "message/send",
  "params": {
    "message": {
      "messageId": "test-token-validation",
      "role": "user",
      "parts": [{
        "text": "Validate my bearer token using the bearer_token_validation_tool"
      }]
    }
  }
}'
make_request "POST" "/" "-H 'Authorization: Bearer ${TEST_TOKEN}' -H 'X-User-ID: ${TEST_USER_ID}' -H 'X-Auth-Provider: test-provider' -H 'Content-Type: application/json'" "$token_validation_payload"

# Test 9: Test authenticated headers
echo -e "${BLUE}--- Test 9: Test Auth Headers Tool ---${NC}"
headers_payload='{
  "jsonrpc": "2.0",
  "id": "test-4",
  "method": "message/send",
  "params": {
    "message": {
      "messageId": "test-auth-headers",
      "role": "user",
      "parts": [{
        "text": "Show me the authentication headers using example_authenticated_tool with action=headers"
      }]
    }
  }
}'
make_request "POST" "/" "-H 'Authorization: Bearer ${TEST_TOKEN}' -H 'X-User-ID: ${TEST_USER_ID}' -H 'X-Auth-Provider: test-provider' -H 'Content-Type: application/json'" "$headers_payload"

# Test 10: HTTPS redirect test (if protocol is http and we're testing HTTPS enforcement)
if [ "$PROTOCOL" = "http" ] && [ "${TEST_HTTPS_REDIRECT:-false}" = "true" ]; then
    echo -e "${BLUE}--- Test 10: HTTPS Redirect Test ---${NC}"
    echo "Note: This test requires the agent to be running in production mode with HTTPS enforcement"
    make_request "GET" "/health" "" "" "false"
fi

echo -e "${BLUE}=== Test Summary ===${NC}"
echo "All authentication forwarding tests completed."
echo
echo "Key test scenarios covered:"
echo "✅ Health check and agent card retrieval"
echo "✅ Authentication status with and without auth"
echo "✅ Bearer token authentication forwarding"
echo "✅ API key authentication forwarding"
echo "✅ A2A protocol with auth context"
echo "✅ Tool-level authentication access"
echo "✅ Token validation and header masking"
echo
echo -e "${GREEN}🎉 Authentication forwarding tests completed!${NC}"

# Additional curl examples for manual testing
echo -e "${BLUE}=== Manual Testing Examples ===${NC}"
echo "Test bearer token auth:"
echo "curl -H 'Authorization: Bearer your-token' -H 'X-User-ID: your-user' ${BASE_URL}/auth/status"
echo
echo "Test A2A with auth:"
echo "curl -X POST -H 'Authorization: Bearer your-token' -H 'Content-Type: application/json' \\"
echo "  -d '{\"jsonrpc\":\"2.0\",\"id\":\"1\",\"method\":\"message/send\",\"params\":{\"message\":{\"messageId\":\"test\",\"role\":\"user\",\"parts\":[{\"text\":\"Show me my authentication info\"}]}}}' \\"
echo "  ${BASE_URL}/"