#!/bin/bash

# Test HTTPS Communication for Simplified Template
# This script tests HTTPS setup and secure communication

set -e

# Configuration
HOST="${HOST:-localhost}"
HTTP_PORT="${HTTP_PORT:-8000}"
HTTPS_PORT="${HTTPS_PORT:-8443}"
CERT_DIR="${CERT_DIR:-./certs}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== Simplified Template HTTPS Testing ===${NC}"
echo

# Function to check if a service is running
check_service() {
    local host="$1"
    local port="$2"
    local protocol="$3"

    echo -e "${YELLOW}Checking ${protocol}://${host}:${port}...${NC}"

    if [ "$protocol" = "https" ]; then
        response=$(curl -k -s -w "HTTPSTATUS:%{http_code}" "https://${host}:${port}/health" 2>/dev/null || echo "HTTPSTATUS:000")
    else
        response=$(curl -s -w "HTTPSTATUS:%{http_code}" "http://${host}:${port}/health" 2>/dev/null || echo "HTTPSTATUS:000")
    fi

    http_status=$(echo "$response" | grep -o "HTTPSTATUS:[0-9]*" | cut -d: -f2)

    if [ "$http_status" -ge 200 ] && [ "$http_status" -lt 300 ]; then
        echo -e "${GREEN}✅ Service is running (HTTP $http_status)${NC}"
        return 0
    else
        echo -e "${RED}❌ Service not available (HTTP $http_status)${NC}"
        return 1
    fi
}

# Function to test SSL certificate
test_ssl_cert() {
    local host="$1"
    local port="$2"

    echo -e "${YELLOW}Testing SSL certificate for ${host}:${port}...${NC}"

    # Test SSL connection
    if echo | openssl s_client -connect "${host}:${port}" -servername "${host}" 2>/dev/null | grep "CONNECTED"; then
        echo -e "${GREEN}✅ SSL connection successful${NC}"

        # Get certificate info
        cert_info=$(echo | openssl s_client -connect "${host}:${port}" -servername "${host}" 2>/dev/null | openssl x509 -noout -dates 2>/dev/null)
        if [ $? -eq 0 ]; then
            echo "Certificate validity:"
            echo "$cert_info"
        fi

        return 0
    else
        echo -e "${RED}❌ SSL connection failed${NC}"
        return 1
    fi
}

# Function to compare HTTP vs HTTPS performance
compare_protocols() {
    local host="$1"
    local endpoint="/health"

    echo -e "${YELLOW}Comparing HTTP vs HTTPS performance...${NC}"

    # HTTP timing
    if check_service "$host" "$HTTP_PORT" "http" >/dev/null 2>&1; then
        http_time=$(curl -s -w "%{time_total}" -o /dev/null "http://${host}:${HTTP_PORT}${endpoint}" 2>/dev/null || echo "0")
        echo "HTTP response time: ${http_time}s"
    else
        echo "HTTP service not available for comparison"
    fi

    # HTTPS timing
    if check_service "$host" "$HTTPS_PORT" "https" >/dev/null 2>&1; then
        https_time=$(curl -k -s -w "%{time_total}" -o /dev/null "https://${host}:${HTTPS_PORT}${endpoint}" 2>/dev/null || echo "0")
        echo "HTTPS response time: ${https_time}s"
    else
        echo "HTTPS service not available for comparison"
    fi
}

# Function to test HTTPS security headers
test_security_headers() {
    local host="$1"
    local port="$2"

    echo -e "${YELLOW}Testing HTTPS security headers...${NC}"

    headers=$(curl -k -s -I "https://${host}:${port}/health" 2>/dev/null || echo "")

    if [ -n "$headers" ]; then
        echo "Response headers:"
        echo "$headers"

        # Check for security headers
        if echo "$headers" | grep -i "strict-transport-security" >/dev/null; then
            echo -e "${GREEN}✅ HSTS header present${NC}"
        else
            echo -e "${YELLOW}⚠️  HSTS header missing${NC}"
        fi

        if echo "$headers" | grep -i "x-content-type-options" >/dev/null; then
            echo -e "${GREEN}✅ X-Content-Type-Options header present${NC}"
        else
            echo -e "${YELLOW}⚠️  X-Content-Type-Options header missing${NC}"
        fi

    else
        echo -e "${RED}❌ Could not retrieve headers${NC}"
    fi
}

# Main testing flow
echo -e "${BLUE}--- Test 1: HTTP Service Check ---${NC}"
if check_service "$HOST" "$HTTP_PORT" "http"; then
    HTTP_AVAILABLE=true
else
    HTTP_AVAILABLE=false
    echo "Note: HTTP service not running, which is expected in production mode"
fi

echo
echo -e "${BLUE}--- Test 2: HTTPS Service Check ---${NC}"
if check_service "$HOST" "$HTTPS_PORT" "https"; then
    HTTPS_AVAILABLE=true
else
    HTTPS_AVAILABLE=false
    echo "Note: HTTPS service not running. Make sure to:"
    echo "1. Generate SSL certificates with: ./deployment/ssl_setup.py"
    echo "2. Set HTTPS_ENABLED=true in .env"
    echo "3. Set SSL_CERT_FILE and SSL_KEY_FILE paths"
    echo "4. Start agent with production environment"
fi

echo
echo -e "${BLUE}--- Test 3: SSL Certificate Validation ---${NC}"
if [ "$HTTPS_AVAILABLE" = true ]; then
    test_ssl_cert "$HOST" "$HTTPS_PORT"
else
    echo "Skipping SSL certificate test (HTTPS service not available)"
fi

echo
echo -e "${BLUE}--- Test 4: Security Headers Test ---${NC}"
if [ "$HTTPS_AVAILABLE" = true ]; then
    test_security_headers "$HOST" "$HTTPS_PORT"
else
    echo "Skipping security headers test (HTTPS service not available)"
fi

echo
echo -e "${BLUE}--- Test 5: Protocol Performance Comparison ---${NC}"
compare_protocols "$HOST"

echo
echo -e "${BLUE}--- Test 6: HTTPS Authentication Test ---${NC}"
if [ "$HTTPS_AVAILABLE" = true ]; then
    echo "Testing HTTPS with authentication..."

    auth_response=$(curl -k -s -H "Authorization: Bearer test-token-123" \
                        -H "X-User-ID: test-user" \
                        "https://${HOST}:${HTTPS_PORT}/auth/status" 2>/dev/null || echo "{}")

    if echo "$auth_response" | grep -q "authenticated"; then
        echo -e "${GREEN}✅ HTTPS authentication test successful${NC}"
        echo "Response: $auth_response" | jq '.' 2>/dev/null || echo "Response: $auth_response"
    else
        echo -e "${RED}❌ HTTPS authentication test failed${NC}"
        echo "Response: $auth_response"
    fi
else
    echo "Skipping HTTPS authentication test (HTTPS service not available)"
fi

echo
echo -e "${BLUE}--- Test 7: Certificate File Verification ---${NC}"
if [ -d "$CERT_DIR" ]; then
    echo "Checking certificate files in $CERT_DIR..."

    if [ -f "$CERT_DIR/localhost.crt" ] && [ -f "$CERT_DIR/localhost.key" ]; then
        echo -e "${GREEN}✅ Certificate files found${NC}"

        # Verify certificate
        if openssl x509 -in "$CERT_DIR/localhost.crt" -text -noout >/dev/null 2>&1; then
            echo -e "${GREEN}✅ Certificate file is valid${NC}"

            # Show certificate details
            echo "Certificate details:"
            openssl x509 -in "$CERT_DIR/localhost.crt" -noout -subject -dates
        else
            echo -e "${RED}❌ Certificate file is invalid${NC}"
        fi

        # Check key file
        if openssl rsa -in "$CERT_DIR/localhost.key" -check -noout >/dev/null 2>&1; then
            echo -e "${GREEN}✅ Private key file is valid${NC}"
        else
            echo -e "${RED}❌ Private key file is invalid${NC}"
        fi

    else
        echo -e "${YELLOW}⚠️  Certificate files not found in $CERT_DIR${NC}"
        echo "Generate certificates with: ./deployment/ssl_setup.py"
    fi
else
    echo -e "${YELLOW}⚠️  Certificate directory $CERT_DIR not found${NC}"
fi

echo
echo -e "${BLUE}=== HTTPS Test Summary ===${NC}"
echo "HTTP service: $([ "$HTTP_AVAILABLE" = true ] && echo "✅ Available" || echo "❌ Not available")"
echo "HTTPS service: $([ "$HTTPS_AVAILABLE" = true ] && echo "✅ Available" || echo "❌ Not available")"

if [ "$HTTPS_AVAILABLE" = true ]; then
    echo -e "${GREEN}🎉 HTTPS testing completed successfully!${NC}"
else
    echo -e "${YELLOW}⚠️  HTTPS not available. Setup instructions:${NC}"
    echo
    echo "1. Generate SSL certificates:"
    echo "   ./deployment/ssl_setup.py --domain localhost"
    echo
    echo "2. Configure environment:"
    echo "   cp .env.example .env"
    echo "   # Edit .env and set:"
    echo "   HTTPS_ENABLED=true"
    echo "   SSL_CERT_FILE=./certs/localhost.crt"
    echo "   SSL_KEY_FILE=./certs/localhost.key"
    echo "   ENVIRONMENT=production"
    echo
    echo "3. Start the agent:"
    echo "   python src/agent.py"
    echo
    echo "4. Test HTTPS:"
    echo "   curl -k https://localhost:8000/health"
fi

echo
echo -e "${BLUE}=== Manual HTTPS Testing Commands ===${NC}"
echo "Test HTTPS health:"
echo "curl -k https://${HOST}:${HTTPS_PORT}/health"
echo
echo "Test HTTPS with auth:"
echo "curl -k -H 'Authorization: Bearer test-token' https://${HOST}:${HTTPS_PORT}/auth/status"
echo
echo "Verify SSL certificate:"
echo "openssl s_client -connect ${HOST}:${HTTPS_PORT} -servername ${HOST}"