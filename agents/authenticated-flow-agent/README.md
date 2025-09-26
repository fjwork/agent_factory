# Authentication Flow Verification Agent

A complete system for testing end-to-end authentication flows in agent factory systems, featuring dual authentication (Bearer tokens + OAuth) and A2A protocol verification.

## 🎯 Overview

This agent tests that authentication context properly flows from clients → orchestrator → remote agents through the A2A protocol.

**Architecture:**
```
Client → Orchestrator Agent → Remote Agent
       Bearer/OAuth         A2A + Auth
```

## 📁 Project Structure

```
authenticated-flow-agent/
├── src/
│   ├── agent.py                      # Main orchestrator agent
│   └── tools/
│       └── auth_verification_tool.py # Auth verification tool
├── auth-verification-remote/         # Remote agent for A2A testing
│   ├── src/
│   │   ├── agent.py                  # Remote agent
│   │   └── tools/
│   │       └── auth_verification_tool.py
│   ├── config/
│   ├── .env
│   └── requirements.txt
├── config/                           # Agent configuration
├── .env                             # Orchestrator environment
├── requirements.txt                 # Python dependencies
├── test_auth_flow.py               # Comprehensive test suite
├── quick_test.py                   # Quick verification test
├── start_agents.sh                 # Easy startup script
└── README.md                       # This file
```

## 🚀 Quick Start

### 1. Setup Environment

```bash
# Navigate to the authenticated-flow-agent directory
cd agents/authenticated-flow-agent

# Verify setup before starting (optional)
python verify_setup.py

# Create and activate Python virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies for orchestrator
pip install -r requirements.txt

# Install dependencies for remote agent
pip install -r auth-verification-remote/requirements.txt
```

### 2. Start Both Agents

```bash
# Start both agents (orchestrator + remote)
./start_agents.sh
```

**Expected Output:**
```
🚀 Starting Authentication Flow Verification Agents
==================================================
🔍 Checking port availability...
✅ Ports 8001 and 8002 are available
🔧 Starting Auth Verification Remote Agent (port 8002)...
✅ Remote agent started with PID: 12345
🔧 Starting Authenticated Flow Agent (port 8001)...
✅ Orchestrator agent started with PID: 12346

🎉 Both agents are starting up!
📋 Remote Agent:      http://localhost:8002
📋 Orchestrator:      http://localhost:8001
```

### 3. Run Quick Verification

```bash
# In a new terminal (keep agents running)
cd agents/authenticated-flow-agent
source venv/bin/activate
python quick_test.py
```

**Expected Output:**
```
🔍 Quick Authentication Flow Test
==================================================
1. Testing health endpoints...
   ✅ Orchestrator (8001) is healthy
   ✅ Remote agent (8002) is healthy
2. Testing agent cards...
   ✅ Orchestrator card: AuthenticatedFlowAgent
   ✅ Remote card: AuthVerificationRemote
3. Testing authentication...
   ✅ Authentication test successful
==================================================
🎉 Quick test completed successfully!
```

### 4. Run Full Test Suite

```bash
python test_auth_flow.py
```

## 🧪 Manual Testing

### Test Local Authentication

```bash
curl -X POST http://localhost:8001/ \
  -H "Authorization: Bearer test-token-123" \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": "1",
    "method": "message/send",
    "params": {
      "message": {
        "role": "user",
        "content": [{"text": "Test local authentication"}]
      }
    }
  }'
```

### Test Remote Delegation

```bash
curl -X POST http://localhost:8001/ \
  -H "Authorization: Bearer test-token-456" \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": "2",
    "method": "message/send",
    "params": {
      "message": {
        "role": "user",
        "content": [{"text": "Test remote authentication by delegating to remote agent"}]
      }
    }
  }'
```

### Check Agent Status

```bash
# Health checks
curl http://localhost:8001/health
curl http://localhost:8002/health

# Agent cards
curl http://localhost:8001/.well-known/agent-card.json
curl http://localhost:8002/.well-known/agent-card.json

# Authentication status
curl http://localhost:8001/auth/dual-status
curl http://localhost:8002/auth/dual-status
```

## 🔧 Configuration

### Environment Variables

Key settings in `.env` files:

```bash
# Agent identity
AGENT_NAME=AuthenticatedFlowAgent
AGENT_DESCRIPTION="Authentication flow testing agent"

# Server ports
A2A_PORT=8001  # Orchestrator
A2A_PORT=8002  # Remote agent

# Authentication
BEARER_TOKEN_VALIDATION=valid  # Always accept tokens for testing
OAUTH_DEFAULT_PROVIDER=google
GOOGLE_OAUTH_CLIENT_ID=your-client-id
GOOGLE_OAUTH_CLIENT_SECRET=your-client-secret

# Remote agent connection
REMOTE_AGENT_URL=http://localhost:8002

# Logging
LOG_LEVEL=DEBUG
```

### Authentication Modes

The system supports both authentication methods:

1. **Bearer Token** (Testing): `Authorization: Bearer <token>`
2. **OAuth Device Flow** (Production): Interactive browser authentication

## ✅ What Gets Tested

### Local Authentication Flow
1. ✅ Bearer token received by orchestrator
2. ✅ Authentication context extracted by DualAuthMiddleware
3. ✅ User context passed to local auth verification tool
4. ✅ Tool receives and prints authentication details

### Remote Authentication Flow
1. ✅ Orchestrator delegates task to remote agent via A2A
2. ✅ Authentication context forwarded through A2A protocol
3. ✅ Remote agent receives authentication in ADK session
4. ✅ Remote tool verifies and prints forwarded auth details

### Expected Authentication Context
```json
{
  "user_id": "user@example.com",
  "provider": "bearer_token",
  "auth_type": "bearer",
  "authenticated": true,
  "token_present": true,
  "token_length": 20,
  "timestamp": "2025-01-26T12:00:00Z"
}
```

## 🛠 Troubleshooting

### Port Already in Use
```bash
# Check what's using the ports
lsof -i :8001
lsof -i :8002

# Kill processes if needed
kill <PID>
```

### Agent Connection Issues
```bash
# Check agents are running
curl http://localhost:8001/health
curl http://localhost:8002/health

# Check logs in terminal where start_agents.sh is running
```

### Authentication Failures
1. Verify `BEARER_TOKEN_VALIDATION=valid` in `.env` files
2. Check OAuth credentials if using OAuth flow
3. Review agent logs for authentication errors

### Dependencies Issues
```bash
# Reinstall dependencies
pip install -r requirements.txt
pip install -r auth-verification-remote/requirements.txt

# Check Python path issues
python -c "import google.adk.agents; print('ADK imported successfully')"
```

## 🔄 Development Workflow

### Making Changes
1. Stop agents: `Ctrl+C` in terminal running `start_agents.sh`
2. Make code changes
3. Restart: `./start_agents.sh`
4. Test: `python quick_test.py`

### Adding New Tests
1. Edit `test_auth_flow.py` for comprehensive tests
2. Edit `quick_test.py` for quick verification tests
3. Add manual curl commands to this README

## 📊 Implementation Details

### Technologies Used
- **Google ADK**: Agent framework with `sub_agents` support
- **A2A Protocol**: Agent-to-Agent communication with auth forwarding
- **DualAuthMiddleware**: Bearer token + OAuth authentication
- **RemoteA2aAgent**: ADK class for remote agent connections
- **AuthenticatedTool**: Base class for OAuth-aware tools

### Key Features
- ✅ **Minimal Changes**: Leverages existing agent-template infrastructure
- ✅ **Real A2A Testing**: Uses actual A2A protocol, not mocks
- ✅ **Token Visibility**: Prints authentication details for verification
- ✅ **Dual Auth Support**: Tests both Bearer tokens and OAuth flows
- ✅ **Production Ready**: Built on proven authentication patterns
- ✅ **Easy Testing**: Automated test suite + manual verification
- ✅ **Clear Documentation**: Step-by-step setup and usage guide

This system provides comprehensive verification that authentication flows work correctly from client requests through to remote agent delegation via the A2A protocol.