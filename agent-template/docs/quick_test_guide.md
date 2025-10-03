# Quick Test Guide: Agent Template with MCP Toolkit and Remote Agent

This guide walks you through testing the complete agent-template setup step by step.

## 🎯 What You'll Test

```
Main Agent (8000) ──────────────→ Remote Agent (8001)
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
pip install Flask PyJWT requests python-dotenv

# Start MCP server
python server.py
```

**✅ Expected Output:**
```
* Running on http://0.0.0.0:8080
* Debug mode: on
```

**✅ Verify MCP Server:**
```bash
# Test health endpoint
curl http://localhost:8080/health
# Should return: {"status": "healthy", "service": "MCP Server"}
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
A2A_PORT=8001
LOG_LEVEL=INFO
EOF

# Start remote agent
python src/agent.py
```

**✅ Expected Output:**
```
INFO - Creating agent: RemoteAgentSample (env: development)
INFO - 🚀 Starting server at http://0.0.0.0:8001
INFO - 📋 Agent Card: http://0.0.0.0:8001/.well-known/agent-card.json
```

**✅ Verify Remote Agent:**
```bash
# Test health endpoint
curl http://localhost:8001/health
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
A2A_PORT=8000
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
    url: "http://localhost:8001"
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
INFO - 🚀 Starting server at http://0.0.0.0:8000
```

**✅ Verify Main Agent:**
```bash
# Test health endpoint
curl http://localhost:8000/health
# Should return: {"status": "healthy"}

# Check agent card
curl http://localhost:8000/.well-known/agent-card.json
```

## 🧪 Run Tests

### Test 1: Native Profile Tool

```bash
# Test profile tool (will require authentication)
curl -X POST http://localhost:8000/a2a/message/send \
  -H "Content-Type: application/json" \
  -d '{
    "context_id": "test-profile-1",
    "content": "Get my user profile information"
  }'
```

**✅ Expected Result:** Should return authentication required message since no OAuth setup yet.

### Test 2: MCP Weather Tool

```bash
# Test MCP weather tool
curl -X POST http://localhost:8000/a2a/message/send \
  -H "Content-Type: application/json" \
  -d '{
    "context_id": "test-weather-1",
    "content": "Get weather for San Francisco"
  }'
```

**✅ Expected Result:** Should attempt to connect to MCP server. May show JWT auth errors (expected without proper GCP setup).

### Test 3: Remote Agent Delegation

```bash
# Test remote agent delegation
curl -X POST http://localhost:8000/a2a/message/send \
  -H "Content-Type: application/json" \
  -d '{
    "context_id": "test-remote-1",
    "content": "Validate authentication using the remote agent"
  }'
```

**✅ Expected Result:** Should delegate to remote agent and return authentication validation results.

### Test 4: Bearer Token Tool

```bash
# Test bearer token printing tool
curl -X POST http://localhost:8000/a2a/message/send \
  -H "Content-Type: application/json" \
  -d '{
    "context_id": "test-token-1",
    "content": "Print bearer token information"
  }'
```

**✅ Expected Result:** Should return bearer token analysis and forwarding status.

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
✅ GET /mcp/tools requests
✅ POST /mcp/call requests
✅ Authentication header processing (may fail without JWT)
```

## 🎯 Success Indicators

### ✅ **All Services Running**
- Main Agent: http://localhost:8000/health
- Remote Agent: http://localhost:8001/health
- MCP Server: http://localhost:8080/health

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
sudo lsof -ti:8000 | xargs kill -9
sudo lsof -ti:8001 | xargs kill -9
sudo lsof -ti:8080 | xargs kill -9
```

### Issue: "Remote agent not found"
```bash
# Verify remote agent config
cat config/remote_agents.yaml

# Check remote agent is running
curl http://localhost:8001/.well-known/agent-card.json
```

### Issue: "MCP connection failed"
```bash
# Check MCP server directly
curl http://localhost:8080/mcp/tools
# May return 401 (auth error) - that's expected without proper JWT
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