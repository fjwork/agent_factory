#!/bin/bash

# Bearer Token Test Setup Script
# This script sets up the environment for testing bearer token forwarding

echo "🚀 Setting up Bearer Token Forwarding Test Environment"
echo ""

# Load existing .env file
if [ -f .env ]; then
    echo "✅ Found existing .env file with configuration"
    source .env
    echo "   - BEARER_TOKEN_VALIDATION: $BEARER_TOKEN_VALIDATION"
    echo "   - A2A_PORT: $A2A_PORT (main agent)"
    echo "   - LOG_LEVEL: $LOG_LEVEL"
else
    echo "❌ No .env file found. Please ensure .env exists with OAuth configuration."
    exit 1
fi

# Set remote agent port (not in main .env)
export REMOTE_A2A_PORT=8002
echo "✅ Set REMOTE_A2A_PORT=8002 for remote agent"

# Add remote agent port to .env if not already there
if ! grep -q "REMOTE_A2A_PORT" .env; then
    echo "" >> .env
    echo "# Remote Agent Configuration (for testing)" >> .env
    echo "REMOTE_A2A_PORT=8002" >> .env
    echo "✅ Added REMOTE_A2A_PORT=8002 to .env file"
fi
echo ""

echo "🧪 Test Environment Ready!"
echo ""
echo "Next steps:"
echo "1. Terminal 1: source venv/bin/activate && python3 src/agent.py                    # Start main agent (port 8001)"
echo "2. Terminal 2: source venv/bin/activate && python3 test_remote_agent.py            # Start remote agent (port 8002)"
echo "3. Terminal 3: source venv/bin/activate && python3 bearer_token_test_client.py     # Run comprehensive test"
echo ""
echo "💡 The test will verify:"
echo "   ✓ Bearer token extraction from Authorization header"
echo "   ✓ Token forwarding to tools via session state"
echo "   ✓ Token forwarding to remote agents via A2A protocol"
echo ""