# Getting Started - Authentication Flow Agent

## 🏃‍♂️ TL;DR - Quick Start

```bash
# 1. Navigate to the agent directory
cd agents/authenticated-flow-agent

# 2. Setup Python environment
python3 -m venv venv
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt
pip install -r auth-verification-remote/requirements.txt

# 4. Start both agents
./start_agents.sh

# 5. In a new terminal, test it works
python quick_test.py
```

## 🎯 What This Does

This agent system tests that authentication (bearer tokens/OAuth) properly flows through:

1. **Client** → sends authenticated request
2. **Orchestrator Agent** (port 8001) → receives auth, tests locally
3. **Remote Agent** (port 8002) → receives auth via A2A protocol

Both agents print authentication details to verify the flow works end-to-end.

## 📋 Expected Output

### When Starting Agents:
```
🚀 Starting Authentication Flow Verification Agents
✅ Remote agent started with PID: 12345
✅ Orchestrator agent started with PID: 12346
📋 Remote Agent:      http://localhost:8002
📋 Orchestrator:      http://localhost:8001
```

### When Running Quick Test:
```
🔍 Quick Authentication Flow Test
1. Testing health endpoints...
   ✅ Orchestrator (8001) is healthy
   ✅ Remote agent (8002) is healthy
2. Testing agent cards...
   ✅ Orchestrator card: AuthenticatedFlowAgent
   ✅ Remote card: AuthVerificationRemote
3. Testing authentication...
   ✅ Authentication test successful
🎉 Quick test completed successfully!
```

## 🔧 Manual Test Commands

```bash
# Test local authentication
curl -X POST http://localhost:8001/ \
  -H "Authorization: Bearer test-token-123" \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":"1","method":"message/send","params":{"message":{"role":"user","content":[{"text":"Test authentication"}]}}}'

# Check health
curl http://localhost:8001/health
curl http://localhost:8002/health
```

## 🛑 Stop Agents

Press `Ctrl+C` in the terminal running `start_agents.sh`

## 📚 Full Documentation

See [README.md](README.md) for complete documentation, troubleshooting, and advanced usage.

---

**What this verifies:** End-to-end authentication flow from client → orchestrator → remote agent via A2A protocol ✅