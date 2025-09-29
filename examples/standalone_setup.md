# Standalone Agent Setup Guide

This guide explains how to set up and run the agent-template as a single, standalone agent without remote agents.

## 📋 Overview

In standalone mode, the agent-template operates as a single OAuth-authenticated agent with:
- Bearer token analysis and forwarding capabilities
- OAuth authentication flow support
- Existing authenticated tools
- No remote agent delegation

## 🚀 Quick Start

### 1. Prerequisites

Ensure you have the following installed:
- Python 3.8+
- Required dependencies (see main README)
- Google ADK installed and configured

### 2. Configuration

The agent will automatically run in standalone mode when:
- No `config/remote_agents.yaml` file exists, OR
- The `remote_agents.yaml` file is empty, OR
- All remote agents in the config are disabled

#### Option A: No Remote Config File (Recommended for Standalone)

Simply ensure that `config/remote_agents.yaml` does not exist:

```bash
# Remove remote agents config if it exists
rm -f config/remote_agents.yaml
```

#### Option B: Empty Remote Config File

Create an empty `config/remote_agents.yaml`:

```yaml
# Empty configuration - agent runs in standalone mode
remote_agents: []
```

#### Option C: Disabled Remote Agents

Keep the config file but disable all agents:

```yaml
remote_agents:
  - name: "data_analysis_agent"
    description: "Handles complex data analysis"
    agent_card_url: "http://localhost:8002/a2a/data_analysis_agent"
    enabled: false  # Disabled

  - name: "notification_agent"
    description: "Sends notifications and alerts"
    agent_card_url: "http://localhost:8003/a2a/notification_agent"
    enabled: false  # Disabled
```

### 3. Starting the Agent

#### Method A: Direct Python Execution

```bash
# Navigate to the agent directory
cd agent-template

# Start the agent
python src/agent.py
```

#### Method B: Using the Start Script

```bash
# Make the script executable
chmod +x start_agent.sh

# Start the agent
./start_agent.sh
```

#### Method C: Development Mode with Hot Reload

```bash
# Start with uvicorn for development
uvicorn src.agent:app --host 0.0.0.0 --port 8001 --reload
```

### 4. Verification

Once started, verify the agent is running correctly:

#### Check Agent Health
```bash
curl http://localhost:8001/health
```

Expected response:
```json
{
  "status": "healthy",
  "mode": "standalone",
  "authentication": "enabled",
  "remote_agents": 0
}
```

#### Check Agent Card
```bash
curl http://localhost:8001/.well-known/agent-card.json
```

#### Test Bearer Token Functionality
```bash
curl -X POST http://localhost:8001/a2a \\
  -H "Content-Type: application/json" \\
  -H "Authorization: Bearer your-test-token" \\
  -d '{
    "jsonrpc": "2.0",
    "id": "test-1",
    "method": "message/send",
    "params": {
      "message": {
        "messageId": "test-msg-1",
        "role": "user",
        "parts": [{"text": "Please analyze my bearer token"}]
      }
    }
  }'
```

## 🔧 Configuration Details

### Environment Variables

Set these environment variables for standalone operation:

```bash
# Required
export AGENT_NAME="AuthenticatedAgent"
export MODEL_NAME="gemini-2.0-flash"

# Authentication (choose one)
export OAUTH_CLIENT_ID="your-oauth-client-id"
export OAUTH_CLIENT_SECRET="your-oauth-client-secret"

# Optional
export AGENT_PORT="8001"
export AGENT_HOST="0.0.0.0"
export LOG_LEVEL="INFO"
```

### Agent Configuration

The main agent config (`config/agent_config.yaml`) remains unchanged:

```yaml
agent:
  name: "AuthenticatedAgent"
  model: "gemini-2.0-flash"
  description: "OAuth-authenticated agent with bearer token support"

authentication:
  oauth:
    enabled: true
    providers:
      - google
  bearer_token:
    enabled: true
```

## 🧪 Testing Standalone Mode

### Automated Testing

Run the standalone tests:

```bash
# Test standalone mode specifically
python testing/test_root_agent.py
```

The test will:
1. Temporarily hide any remote config
2. Create agent in standalone mode
3. Verify no sub-agents are loaded
4. Test bearer token functionality
5. Restore original config

### Manual Testing

#### 1. Basic Health Check
```bash
curl http://localhost:8001/health
```

#### 2. OAuth Flow Testing
Visit `http://localhost:8001/auth/login` in your browser to test OAuth flow.

#### 3. Bearer Token Testing
```bash
# Test with a sample bearer token
curl -X POST http://localhost:8001/a2a \\
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..." \\
  -H "Content-Type: application/json" \\
  -d '{
    "jsonrpc": "2.0",
    "id": "test",
    "method": "message/send",
    "params": {
      "message": {
        "messageId": "test-msg",
        "role": "user",
        "parts": [{"text": "Hello, please use your bearer token tool"}]
      }
    }
  }'
```

## 📊 Expected Behavior

### Agent Startup Logs
```
INFO - Creating agent: AuthenticatedAgent
INFO - No remote_agents.yaml found - running in single agent mode
INFO - Created agent with 0 remote sub-agents
INFO - Starting server on 0.0.0.0:8001
INFO - Agent Card: http://0.0.0.0:8001/.well-known/agent-card.json
```

### Agent Capabilities in Standalone Mode

The agent will have:
- ✅ OAuth authentication flows
- ✅ Bearer token analysis tools
- ✅ All existing authenticated tools
- ✅ A2A server capability (for future remote agents)
- ❌ No remote agent delegation
- ❌ No sub-agents

### Agent Instructions

In standalone mode, the agent's instructions will be:

```
You are an AI assistant with secure OAuth authentication capabilities.

Your primary capabilities:
- Secure OAuth authentication with multiple providers
- Access to authenticated APIs and user data
- Bearer token analysis and forwarding

You operate as a standalone agent without remote delegation capabilities.
```

## 🔍 Troubleshooting

### Common Issues

#### 1. Agent Shows Remote Agents When Expected Standalone

**Problem**: Agent loads remote agents when you expect standalone mode.

**Solution**:
- Check if `config/remote_agents.yaml` exists
- Verify all agents are disabled (`enabled: false`)
- Check for typos in the YAML file

#### 2. Authentication Not Working

**Problem**: OAuth or bearer token authentication fails.

**Solution**:
- Verify OAuth client ID and secret are set
- Check that authentication middleware is properly configured
- Ensure the authentication endpoints are accessible

#### 3. Port Already in Use

**Problem**: Agent fails to start due to port conflict.

**Solution**:
```bash
# Check what's using port 8001
lsof -i :8001

# Kill the process or use a different port
export AGENT_PORT="8002"
python src/agent.py
```

#### 4. Missing Dependencies

**Problem**: Import errors or missing modules.

**Solution**:
```bash
# Install dependencies
pip install -r requirements.txt

# Verify ADK installation
python -c "import google.adk; print('ADK installed')"
```

### Debug Mode

Enable debug logging for troubleshooting:

```bash
export LOG_LEVEL="DEBUG"
python src/agent.py
```

This will provide detailed logs about:
- Configuration loading
- Remote agent discovery attempts
- Authentication flow details
- Tool execution

## 📚 Next Steps

Once you have the standalone agent working:

1. **Test OAuth Flow**: Visit the login endpoint to test OAuth authentication
2. **Test Bearer Tokens**: Use curl or Postman to test bearer token functionality
3. **Integration**: Integrate with your existing systems
4. **Monitoring**: Set up logging and monitoring for production use

For multi-agent setup with remote agents, see the [Multi-Agent Setup Guide](multi_agent_setup.md).

## 🔗 Related Documentation

- [Multi-Agent Setup Guide](multi_agent_setup.md)
- [Testing Documentation](../testing/README.md)
- [Troubleshooting Guide](troubleshooting.md)
- [Configuration Reference](configuration_reference.md)