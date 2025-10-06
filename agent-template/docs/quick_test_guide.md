# Quick Test Guide: Agent Template with MCP Toolkit and Remote Agent

This guide walks you through testing the complete agent-template setup step by step.

## 🎯 What You'll Test

```
Main Agent (8001) ──────────────→ Remote Agent (8002)
       │                         [auth_validation_tool]
       │
       └─────────────────────────→ MCP Server (8080)
                                   [weather_tool, news_tool]
```

**Components:**
- **Main Agent**: Your agent-template with tool registry, MCP toolkit, profile tool
- **Remote Agent**: `remote-agent-sample` for A2A testing
- **MCP Server**: Example server with weather and news tools

## 🚀 Step-by-Step Testing

### Step 1: Start MCP Server (Terminal 1)

```bash
# Navigate to MCP server
cd /usr/local/google/home/flammoglia/aitests/agent_factory/example-mcp-server

# Install dependencies if needed
pip install -r requirements.txt

# Start the proper MCP server (NOT the legacy server.py)
python mcp_server.py
```

**✅ Expected Output:**
```
INFO - Starting MCP Server...
INFO - Available tools: get_weather, search_news, health_check
INFO - MCP endpoint: http://localhost:8080/mcp
INFO - Health check: Use MCP protocol
INFO - Started server process...
INFO - Uvicorn running on http://0.0.0.0:8080
```

**✅ Verify MCP Server:**
```bash
# The MCP server uses MCP protocol, not REST endpoints
# Verify it's running by checking the process
ps aux | grep mcp_server
# Or check if port 8080 is listening
lsof -i :8080
```

### Step 2: Start Remote Agent (Terminal 2)

```bash
# Navigate to remote agent
cd /usr/local/google/home/flammoglia/aitests/agent_factory/agents/remote-agent-sample

# Create environment file
cat > .env << 'EOF'
AGENT_NAME=RemoteAgentSample
ENVIRONMENT=development
A2A_HOST=0.0.0.0
A2A_PORT=8002
LOG_LEVEL=INFO
EOF

# Start remote agent
python src/agent.py
```

**✅ Expected Output:**
```
INFO - Creating agent: RemoteAgentSample (env: development)
INFO - 🚀 Starting server at http://0.0.0.0:8002
INFO - 📋 Agent Card: http://0.0.0.0:8002/.well-known/agent-card.json
```

**✅ Verify Remote Agent:**
```bash
# Test health endpoint
curl http://localhost:8002/health
# Should return: {"status": "healthy"}
```

### Step 3: Configure Main Agent (Terminal 3)

```bash
# Navigate to agent template
cd /usr/local/google/home/flammoglia/aitests/agent_factory/agent-template

# Create environment file
cat > .env << 'EOF'
AGENT_NAME=MainAgent
ENVIRONMENT=development
A2A_HOST=0.0.0.0
A2A_PORT=8001
LOG_LEVEL=INFO

# MCP Configuration
MCP_SERVER_URL=http://localhost:8080
TOKEN_REFRESH_THRESHOLD_MINS=15
ENABLE_WEATHER_MCP=true
EOF

# Configure remote agents
cat > config/remote_agents.yaml << 'EOF'
remote_agents:
  - name: "remote_agent_sample"
    url: "http://localhost:8002"
    description: "Sample remote agent for testing authentication forwarding"
    capabilities:
      - "authentication_validation"
      - "bearer_token_testing"
EOF
```

### Step 4: Start Main Agent (Terminal 3)

```bash
# Start main agent
python src/agent.py
```

**✅ Expected Output:**
```
INFO - Creating agent: MainAgent (env: development)
INFO - 📋 Loaded 3 tools from registry
INFO - 🔧 Created MCP auth callback for 1 toolsets
INFO - ✅ Created agent with 4 total tools:
INFO -    - 3 traditional authenticated tools
INFO -    - 1 MCP toolsets
INFO - ✅ Agent has 1 remote sub-agents:
INFO -    - remote_agent_sample: Sample remote agent for testing authentication forwarding
INFO - 🚀 Starting server at http://0.0.0.0:8001
```

**✅ Verify Main Agent:**
```bash
# Test health endpoint
curl http://localhost:8001/health
# Should return: {"status": "healthy"}

# Check agent card
curl http://localhost:8001/.well-known/agent-card.json
```

## 🧪 Run Tests

### Test 1: Native Profile Tool

```bash
# Test profile tool (will require authentication)
curl -X POST http://localhost:8001/ \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": "test-profile-1",
    "method": "message/send",
    "params": {
      "context_id": "test-profile-1",
      "message": {
        "messageId": "profile-test",
        "role": "user",
        "parts": [{
          "text": "Get my user profile information"
        }]
      }
    }
  }'
```

**✅ Expected Result:** Should return authentication required message since no OAuth setup yet.

### Test 2: MCP Weather Tool (with Bearer Token)

```bash
# Test MCP weather tool with bearer token
curl -X POST http://localhost:8001/ \
  -H "Authorization: Bearer test-token-123" \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": "test-weather-1",
    "method": "message/send",
    "params": {
      "context_id": "test-weather-1",
      "message": {
        "messageId": "weather-test",
        "role": "user",
        "parts": [{
          "text": "Get weather for San Francisco"
        }]
      }
    }
  }'
```

**✅ Expected Result:** Should attempt to connect to MCP server and forward the bearer token. May show JWT auth errors (expected without proper GCP setup), but auth context should be passed through.

### Test 3: Remote Agent Delegation (with Bearer Token)

```bash
# Test remote agent delegation with bearer token for authentication forwarding
curl -X POST http://localhost:8001/ \
  -H "Authorization: Bearer test-token-123" \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": "test-remote-1",
    "method": "message/send",
    "params": {
      "context_id": "test-remote-1",
      "message": {
        "messageId": "remote-test",
        "role": "user",
        "parts": [{
          "text": "Validate authentication using the remote agent"
        }]
      }
    }
  }'
```

**✅ Expected Result:** Should delegate to remote agent with the bearer token forwarded. The remote agent should receive and validate the authentication context.

### Test 4: Bearer Token Tool (with Bearer Token)

```bash
# Test bearer token printing tool with authentication
curl -X POST http://localhost:8001/ \
  -H "Authorization: Bearer test-token-123" \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": "test-token-1",
    "method": "message/send",
    "params": {
      "context_id": "test-token-1",
      "message": {
        "messageId": "token-test",
        "role": "user",
        "parts": [{
          "text": "Print bearer token information"
        }]
      }
    }
  }'
```

**✅ Expected Result:** Should execute the bearer token tool and display information about the authentication context being forwarded.

### Test 5: Simple Test Tool (No Authentication)

```bash
# Test simple MCP tool without authentication (basic connectivity test)
curl -X POST http://localhost:8001/ \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": "test-simple-1",
    "method": "message/send",
    "params": {
      "context_id": "test-simple-1",
      "message": {
        "messageId": "simple-test",
        "role": "user",
        "parts": [{
          "text": "Run simple test tool"
        }]
      }
    }
  }'
```

**✅ Expected Result:** Should successfully execute the simple_test tool and return a success message, proving basic MCP connectivity works.

## 🔍 What to Look For

### In Main Agent Logs (Terminal 3):
```
✅ Tool registry loading messages
✅ MCP toolset initialization
✅ Remote agent discovery
✅ A2A requests and responses
✅ Authentication callback execution
```

### In Remote Agent Logs (Terminal 2):
```
✅ A2A requests received
✅ Tool execution (auth_validation_tool)
✅ Response sent back to main agent
```

### In MCP Server Logs (Terminal 1):
```
✅ MCP session establishment
✅ Tools list requests (tools/list)
✅ Tool call requests (tools/call)
✅ JWT authentication processing and user identification
```

## 🎯 Success Indicators

### ✅ **All Services Running**
- Main Agent: http://localhost:8001/health
- Remote Agent: http://localhost:8002/health
- MCP Server: Running on port 8080 (check with `lsof -i :8080`)

### ✅ **Tool Discovery Working**
- Main agent logs show "Loaded X tools from registry"
- MCP toolset initialized successfully
- Remote agent detected and configured

### ✅ **A2A Communication Working**
- Remote agent receives requests from main agent
- Responses successfully returned
- Authentication context attempted to forward

### ✅ **MCP Integration Working**
- MCP server receives tool discovery requests
- Tool calls attempted (auth may fail - that's expected)
- Connection established between agent and MCP server

## 🚨 Common Issues & Quick Fixes

### Issue: "Port already in use"
```bash
# Kill processes on ports
sudo lsof -ti:8001 | xargs kill -9
sudo lsof -ti:8002 | xargs kill -9
sudo lsof -ti:8080 | xargs kill -9
```

### Issue: "Remote agent not found"
```bash
# Verify remote agent config
cat config/remote_agents.yaml

# Check remote agent is running
curl http://localhost:8002/.well-known/agent-card.json
```

### Issue: "MCP connection failed"
```bash
# Check MCP server is running
lsof -i :8080
# MCP server uses protocol-level communication, not REST endpoints
# Connection issues usually mean server isn't running or port conflicts
```

### Issue: "JWT authentication failed"
```bash
# This is EXPECTED without Google Cloud credentials
# The test verifies connections work, not full auth flow
```

## ✅ Test Complete!

If you see:
- ✅ All 3 services running on their ports
- ✅ Main agent loading tools from registry
- ✅ Remote agent receiving A2A requests
- ✅ MCP server receiving connection attempts

**Your integration is working!** 🎉

The authentication errors are expected without full OAuth/JWT setup. The important part is that all components are communicating correctly.