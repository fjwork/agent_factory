# Complete Testing Guide: Agent Template with Remote Agents and MCP Toolkit

This guide provides step-by-step instructions to test the complete agent template setup including:
- Main agent with tool registry
- Remote agent (`remote-agent-sample`)
- Native tools (existing tools)
- MCP toolkit with sample MCP server

## 🎯 Testing Architecture

```
┌─────────────────┐    A2A Protocol    ┌─────────────────┐
│ Main Agent      │ ──────────────────→ │ Remote Agent    │
│ (Port 8000)     │                     │ (Port 8001)     │
│                 │                     │                 │
│ - Tool Registry │                     │ - Auth Tool     │
│ - MCP Toolkit   │                     │ - Example Tool  │
│ - Native Tools  │                     │                 │
└─────────┬───────┘                     └─────────────────┘
          │
          │ HTTP/JWT
          ▼
┌─────────────────┐
│ MCP Server      │
│ (Port 8080)     │
│                 │
│ - Weather Tool  │
│ - News Tool     │
└─────────────────┘
```

## 📋 Prerequisites

1. **Python Environment**: Python 3.8+ with virtual environment
2. **Google Cloud Credentials**: For JWT token generation
3. **Network Access**: Ports 8000, 8001, 8080 available locally

## 🚀 Step-by-Step Setup

### Step 1: Set Up the MCP Server

First, start the example MCP server that provides external tools.

```bash
# Terminal 1 - MCP Server
cd /path/to/agent_factory/example-mcp-server

# Install dependencies
pip install -r requirements.txt

# Start MCP server
python mcp_server.py

# Verify it's running (MCP server uses protocol-level communication)
lsof -i :8080
```

**Expected Output:**
```
* Running on http://0.0.0.0:8080
* Debug mode: on
```

### Step 2: Configure Remote Agent

Set up the remote agent sample to run on port 8001.

```bash
# Terminal 2 - Remote Agent Setup
cd /path/to/agent_factory/agents/remote-agent-sample

# Create .env file for remote agent
cat > .env << EOF
AGENT_NAME=RemoteAgentSample
ENVIRONMENT=development
A2A_HOST=0.0.0.0
A2A_PORT=8001
LOG_LEVEL=INFO
EOF

# Install dependencies (if not already done)
pip install -r requirements.txt

# Start remote agent
python src/agent.py
```

**Expected Output:**
```
INFO - Creating agent: RemoteAgentSample (env: development)
INFO - 🚀 Starting server at http://0.0.0.0:8001
INFO - 📋 Agent Card: http://0.0.0.0:8001/.well-known/agent-card.json
```

### Step 3: Configure Main Agent with Remote Agents

Configure the main agent to use the remote agent and MCP server.

```bash
# Terminal 3 - Main Agent Setup
cd /path/to/agent_factory/agent-template

# Create .env file for main agent
cat > .env << EOF
AGENT_NAME=MainAgent
ENVIRONMENT=development
A2A_HOST=0.0.0.0
A2A_PORT=8000
LOG_LEVEL=INFO

# MCP Server Configuration
MCP_SERVER_URL=http://localhost:8080
TOKEN_REFRESH_THRESHOLD_MINS=15
ENABLE_WEATHER_MCP=true

# Google Cloud for JWT tokens (adjust path as needed)
GOOGLE_APPLICATION_CREDENTIALS=/path/to/your-service-account.json
EOF

# Configure remote agents
cat > config/remote_agents.yaml << EOF
remote_agents:
  - name: "remote_agent_sample"
    url: "http://localhost:8001"
    description: "Sample remote agent for testing authentication forwarding"
    capabilities:
      - "authentication_validation"
      - "bearer_token_testing"
EOF

# Install dependencies (if not already done)
pip install -r requirements.txt
```

### Step 4: Verify Tool Registry Configuration

Check that the tool registry and MCP configurations are properly set up.

```bash
# Verify tool registry config exists
cat config/tool_registry.yaml

# Verify MCP toolsets config exists
cat config/mcp_toolsets.yaml

# Should show weather_toolset pointing to localhost:8080
```

### Step 5: Start Main Agent

Start the main agent with full integration.

```bash
# In Terminal 3 (agent-template directory)
python src/agent.py
```

**Expected Output:**
```
INFO - Creating agent: MainAgent (env: development)
INFO - 📋 Loaded 2 tools from registry
INFO - 🔧 Created MCP auth callback for 1 toolsets
INFO - ✅ Created agent with 3 total tools:
INFO -    - 2 traditional authenticated tools
INFO -    - 1 MCP toolsets
INFO - ✅ Agent has 1 remote sub-agents:
INFO -    - remote_agent_sample: Sample remote agent for testing authentication forwarding
INFO - 🚀 Starting server at http://0.0.0.0:8000
```

## 🧪 Testing Scenarios

### Test 1: Verify All Services Are Running

```bash
# Test main agent
curl http://localhost:8000/health
# Expected: {"status": "healthy"}

# Test remote agent
curl http://localhost:8001/health
# Expected: {"status": "healthy"}

# Test MCP server
curl http://localhost:8080/health
# Expected: {"status": "healthy", "service": "MCP Server"}

# Check agent cards
curl http://localhost:8000/.well-known/agent-card.json
curl http://localhost:8001/.well-known/agent-card.json
```

### Test 2: Test Native Tools (Without Authentication)

Test the built-in tools from the tool registry.

```bash
# Test native example tool via A2A
curl -X POST http://localhost:8000/a2a/message/send \
  -H "Content-Type: application/json" \
  -d '{
    "context_id": "test-native-1",
    "content": "Test the example_tool with action get_user_info"
  }'

# Test profile tool via A2A
curl -X POST http://localhost:8000/a2a/message/send \
  -H "Content-Type: application/json" \
  -d '{
    "context_id": "test-native-2",
    "content": "Get my user profile information using the profile tool"
  }'
```

**Expected Behavior:**
- Tool should execute but show authentication required message
- Response should indicate OAuth authentication needed

### Test 3: Test MCP Toolkit (Without Authentication)

Test the MCP server integration.

```bash
# Test MCP weather tool via main agent
curl -X POST http://localhost:8000/a2a/message/send \
  -H "Content-Type: application/json" \
  -d '{
    "context_id": "test-mcp-1",
    "content": "Get weather for San Francisco using the weather tool"
  }'
```

**Expected Behavior:**
- Should attempt to connect to MCP server
- May fail on JWT authentication (expected without proper auth setup)
- Check logs for MCP connection attempts

### Test 4: Test Remote Agent Communication

Test A2A protocol with remote agent.

```bash
# Test delegating to remote agent
curl -X POST http://localhost:8000/a2a/message/send \
  -H "Content-Type: application/json" \
  -d '{
    "context_id": "test-remote-1",
    "content": "Delegate authentication validation to the remote agent"
  }'
```

**Expected Behavior:**
- Main agent should identify need for remote agent
- Should delegate to remote_agent_sample
- Remote agent should execute auth validation tool
- Response should come back through main agent

### Test 5: Test Tool Discovery

Verify that all tools are properly discovered and cached.

```bash
# Check logs for tool loading messages
# In main agent logs, look for:
# - "Loaded X tools from registry"
# - "Created MCP auth callback"
# - Tool discovery from MCP server

# In MCP server logs, look for:
# - GET /mcp/tools requests
# - Authentication header processing
```

## 🔍 Debugging and Troubleshooting

### Common Issues and Solutions

#### 1. MCP Server Connection Issues
```bash
# Check MCP server is accessible
curl http://localhost:8080/mcp/tools

# If it fails, check:
# - MCP server is running on port 8080
# - No firewall blocking the port
# - Check MCP server logs for errors
```

#### 2. Remote Agent Not Found
```bash
# Verify remote agent configuration
cat config/remote_agents.yaml

# Check remote agent is running
curl http://localhost:8001/.well-known/agent-card.json

# Verify main agent can reach remote agent
curl -v http://localhost:8001/health
```

#### 3. JWT Authentication Issues
```bash
# Check Google Cloud credentials
echo $GOOGLE_APPLICATION_CREDENTIALS

# Test JWT token generation
gcloud auth application-default print-access-token

# Check MCP server logs for auth errors
```

#### 4. Tool Registry Issues
```bash
# Check tool registry configuration
python -c "
from agent_template.src.tools.tool_registry import get_tool_registry
registry = get_tool_registry('config')
print(registry.get_tool_status())
"
```

### Debug Mode

Enable detailed logging for troubleshooting:

```bash
# Set debug logging
export LOG_LEVEL=DEBUG

# Restart all services with debug logging
python src/agent.py  # Will show detailed tool loading and MCP requests
```

## 📊 Expected Results

After completing all steps, you should have:

1. **3 Running Services:**
   - Main Agent (port 8000) with tool registry and MCP integration
   - Remote Agent (port 8001) for A2A testing
   - MCP Server (port 8080) providing external tools

2. **Tool Integration:**
   - Native tools from tool registry (example_tool, bearer_token_print_tool, profile_tool)
   - MCP tools from external server (get_weather, search_news)
   - Remote agent tools via A2A protocol (auth_validation_tool)

3. **Authentication Flow:**
   - JWT tokens automatically generated for MCP server
   - OAuth context forwarded to remote agents
   - Bearer token authentication for A2A communication

4. **Successful Test Responses:**
   - Tools execute and return structured responses
   - Authentication context properly forwarded
   - MCP server tools accessible through main agent
   - Remote agent delegation working

## 🎓 Next Steps

Once basic testing is complete:

1. **Add OAuth Authentication:** Set up proper OAuth flow for authenticated testing
2. **Custom Tools:** Add your own tools to the tool registry
3. **Additional MCP Servers:** Create specialized MCP servers for your use cases
4. **Production Deployment:** Use deployment configurations for cloud environments

## 📝 Logs to Monitor

**Main Agent Logs:**
- Tool registry loading
- MCP toolset initialization
- Remote agent discovery
- Authentication callback execution

**Remote Agent Logs:**
- A2A requests received
- Authentication context forwarding
- Tool execution results

**MCP Server Logs:**
- Tool discovery requests
- JWT authentication validation
- Tool execution calls

This testing setup demonstrates the complete agent template architecture with all three integration points working together.