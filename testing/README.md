# Testing Documentation

This document provides comprehensive guidance for testing the agent-template with optional remote agents and authentication forwarding.

## 📋 Overview

The testing framework provides:
- **Modular Testing**: Separate test scripts for different components
- **Authentication Verification**: Tests for bearer token and OAuth forwarding
- **End-to-End Testing**: Complete workflows across multiple agents
- **Automated Test Utilities**: Helper classes for common testing scenarios

## 🗂️ Test Structure

```
testing/
├── README.md                          # This documentation
├── test_root_agent.py                 # Root agent tests (standalone + multi-agent)
├── test_auth_forwarding.py            # End-to-end authentication forwarding tests
├── test_remote_agents/                # Individual remote agent tests
│   ├── test_data_analysis_agent.py
│   ├── test_notification_agent.py
│   └── test_approval_agent.py
├── remote_agents/                     # Sample remote agents for testing
│   ├── data_analysis_agent/
│   ├── notification_agent/
│   └── approval_agent/
└── utils/                             # Testing utilities
    ├── test_client.py                 # Authenticated test client
    └── auth_test_utils.py             # Authentication testing helpers
```

## 🚀 Quick Start

### Prerequisites

1. **Environment Setup**:
   ```bash
   cd agent-template
   export PYTHONPATH="${PYTHONPATH}:$(pwd)/src:$(pwd)/testing"
   ```

2. **Dependencies**:
   ```bash
   pip install -r requirements.txt
   pip install pytest httpx  # Additional test dependencies
   ```

### Running Tests

#### 1. Root Agent Tests (Standalone and Multi-Agent)

```bash
# Test root agent in both modes
python testing/test_root_agent.py
```

**What it tests**:
- Agent creation in standalone mode (no remote agents)
- Agent creation in multi-agent mode (with remote agents)
- Bearer token functionality
- Agent health and basic functionality

**Expected output**:
```
🚀 Starting Root Agent Tests
=============================================================
🏥 Testing Agent Health and Basic Functionality
✅ Agent creation successful
✅ Agent has required attributes
✅ Agent has 2 tools available
✅ Agent has proper instructions
✅ Health and basic functionality test completed

🧪 Testing Root Agent - Standalone Mode
✅ Root agent created in standalone mode (0 sub-agents)
✅ Test token created and verified
✅ Found 1 bearer token related tools
✅ Standalone mode test completed successfully

🧪 Testing Root Agent - Multi-Agent Mode
✅ Root agent created with 3 remote sub-agents:
   1. data_analysis_agent: Handles complex data analysis...
   2. notification_agent: Sends notifications, alerts...
   3. approval_agent: Handles approval workflows...
✅ Multi-agent mode test completed successfully
```

#### 2. Individual Remote Agent Tests

```bash
# Test each remote agent individually
python testing/test_remote_agents/test_data_analysis_agent.py
python testing/test_remote_agents/test_notification_agent.py
python testing/test_remote_agents/test_approval_agent.py
```

**What it tests**:
- Agent server startup and health
- Agent card accessibility
- Bearer token context verification
- Tool functionality
- Authentication forwarding verification

**Expected output example**:
```
🚀 Starting Data Analysis Agent Tests
=============================================================
🚀 Starting Data Analysis Agent on localhost:8002
✅ Data Analysis Agent started successfully
🏥 Testing agent health...
✅ Health check passed
📋 Testing agent card...
✅ Agent card accessible: data_analysis_agent
🔑 Testing bearer token analysis...
✅ Bearer token analysis working correctly
📊 Testing data analysis tool...
   Testing case 1: Please analyze sales_data with summary analysis...
   ✅ Test case 1 passed
   Testing case 2: Please perform trends analysis on user_data...
   ✅ Test case 2 passed
✅ Data analysis tool functionality verified
🔐 Testing authentication verification...
✅ Authentication verification successful
🛑 Stopping Data Analysis Agent...
✅ Data Analysis Agent stopped
```

#### 3. End-to-End Authentication Forwarding Tests

```bash
# Start the root agent first (in separate terminal)
python src/agent.py

# Then run auth forwarding tests
python testing/test_auth_forwarding.py
```

**What it tests**:
- Bearer token forwarding from root to remote agents
- OAuth context forwarding
- Multi-agent delegation chains
- Authentication context preservation

**Expected output**:
```
🚀 Starting Comprehensive Authentication Forwarding Tests
=======================================================================
🚀 Starting all remote agents for auth forwarding tests...
✅ All remote agents started and healthy
⏳ Checking root agent availability...
✅ Root agent is ready

🔑 BEARER TOKEN FORWARDING TESTS
=======================================================================
🔑 Testing Bearer Token Forwarding to data_analysis_agent
✅ Bearer token successfully forwarded to data_analysis_agent

🔐 OAUTH CONTEXT FORWARDING TESTS
=======================================================================
🔐 Testing OAuth Context Forwarding to data_analysis_agent (provider: google)
✅ OAuth context successfully forwarded to data_analysis_agent

🔗 MULTI-AGENT DELEGATION CHAIN TEST
=======================================================================
🔗 Testing Multi-Agent Delegation Chain with Authentication
✅ Multi-agent delegation chain with authentication successful
```

## 🧪 Test Categories

### 1. Unit Tests

Test individual components in isolation:

```bash
# Test specific utilities
python -c "
from testing.utils.auth_test_utils import BearerTokenGenerator
gen = BearerTokenGenerator()
token = gen.create_test_token('test@example.com')
print(f'✅ Token generated: {token[:50]}...')
"

# Test configuration loading
python -c "
from src.agent_factory.remote_agent_factory import RemoteAgentFactory
factory = RemoteAgentFactory()
print('✅ RemoteAgentFactory created successfully')
"
```

### 2. Integration Tests

Test component interactions:

```bash
# Test root agent with remote agent loading
python -c "
import asyncio
from src.agent import create_agent

async def test():
    agent = await create_agent()
    sub_count = len(agent.sub_agents) if agent.sub_agents else 0
    print(f'✅ Agent created with {sub_count} sub-agents')

asyncio.run(test())
"
```

### 3. End-to-End Tests

Test complete workflows:

```bash
# Complete authentication forwarding workflow
python testing/test_auth_forwarding.py
```

### 4. Performance Tests

Test response times and throughput:

```bash
# Test agent response time
time python -c "
import asyncio
from testing.utils.test_client import AuthenticatedTestClient

async def test():
    client = AuthenticatedTestClient('http://localhost:8001')
    result = await client.test_health()
    print(f'Health check: {result}')

asyncio.run(test())
"
```

## 🔧 Testing Utilities

### AuthenticatedTestClient

A comprehensive test client for making authenticated requests:

```python
from testing.utils.test_client import AuthenticatedTestClient

# Create client
client = AuthenticatedTestClient("http://localhost:8001")

# Test health
health = await client.test_health()

# Test with bearer token
result = await client.send_authenticated_message(
    message="Test message",
    bearer_token="your-test-token"
)

# Test with OAuth context
result = await client.send_authenticated_message(
    message="Test message",
    user_id="test@example.com",
    oauth_context={"provider": "google", "token": "oauth-token"}
)
```

### BearerTokenGenerator

Generate test bearer tokens with various configurations:

```python
from testing.utils.auth_test_utils import BearerTokenGenerator

gen = BearerTokenGenerator()

# Basic token
token = gen.create_test_token("user@example.com")

# Token with specific scopes
token = gen.create_test_token(
    user_id="user@example.com",
    scopes=["read", "write", "admin"]
)

# Expired token for negative testing
expired_token = gen.create_expired_token("user@example.com")

# Decode token for verification
payload = gen.decode_test_token(token)
```

### OAuthContextGenerator

Generate test OAuth contexts:

```python
from testing.utils.auth_test_utils import OAuthContextGenerator

gen = OAuthContextGenerator()

# Google OAuth context
context = gen.create_oauth_context(
    provider="google",
    user_id="user@example.com"
)

# GitHub OAuth context
context = gen.create_oauth_context(
    provider="github",
    user_id="user@example.com"
)
```

### AuthAssertions

Helper methods for authentication-related assertions:

```python
from testing.utils.auth_test_utils import AuthAssertions

# Assert auth context was forwarded
AuthAssertions.assert_auth_context_forwarded(response, "data_analysis_agent")

# Assert bearer token was present
AuthAssertions.assert_bearer_token_present(response)

# Assert OAuth context was present
AuthAssertions.assert_oauth_context_present(response, "google")
```

## 📊 Test Configuration

### Environment Variables for Testing

```bash
# Test-specific environment variables
export LOG_LEVEL="DEBUG"
export TEST_MODE="true"
export MOCK_EXTERNAL_SERVICES="true"
export AUTO_APPROVE_WORKFLOWS="true"

# Test agent ports
export AGENT_PORT="8001"
export DATA_ANALYSIS_PORT="8002"
export NOTIFICATION_PORT="8003"
export APPROVAL_PORT="8004"

# Test authentication
export OAUTH_CLIENT_ID="test-client-id"
export OAUTH_CLIENT_SECRET="test-client-secret"
export TEST_BEARER_TOKEN="test-token-12345"
```

### Test Configuration Files

Use specific configurations for testing:

```bash
# Use minimal config for faster tests
cp examples/configurations/minimal_remote_agents.yaml config/remote_agents.yaml

# Or use complete config for full testing
cp examples/configurations/complete_remote_agents.yaml config/remote_agents.yaml

# Or use development config with debug options
cp examples/configurations/development_remote_agents.yaml config/remote_agents.yaml
```

## 🐛 Debugging Tests

### Enable Debug Logging

```bash
export LOG_LEVEL="DEBUG"
python testing/test_root_agent.py
```

### Test Individual Components

```python
# Debug specific test client functionality
import asyncio
from testing.utils.test_client import AuthenticatedTestClient

async def debug_client():
    client = AuthenticatedTestClient("http://localhost:8001")

    # Test basic connectivity
    health = await client.test_health()
    print(f"Health: {health}")

    # Test agent card
    card = await client.get_agent_card()
    print(f"Agent card: {card}")

asyncio.run(debug_client())
```

### Inspect Token Generation

```python
from testing.utils.auth_test_utils import BearerTokenGenerator

gen = BearerTokenGenerator()
token = gen.create_test_token("debug@example.com")
payload = gen.decode_test_token(token)

print(f"Token: {token}")
print(f"Payload: {payload}")
```

### Manual API Testing

```bash
# Test root agent directly
curl -X POST http://localhost:8001/a2a \\
  -H "Content-Type: application/json" \\
  -H "Authorization: Bearer test-token-123" \\
  -d '{
    "jsonrpc": "2.0",
    "id": "debug-test",
    "method": "message/send",
    "params": {
      "message": {
        "messageId": "debug-msg",
        "role": "user",
        "parts": [{"text": "Debug test message"}]
      }
    }
  }'
```

## 🔄 Continuous Integration

### GitHub Actions Example

```yaml
name: Agent Tests
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: 3.8

    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install pytest httpx

    - name: Run root agent tests
      run: python testing/test_root_agent.py

    - name: Run remote agent tests
      run: |
        python testing/test_remote_agents/test_data_analysis_agent.py
        python testing/test_remote_agents/test_notification_agent.py
        python testing/test_remote_agents/test_approval_agent.py

    - name: Run integration tests
      run: |
        python src/agent.py &
        sleep 10
        python testing/test_auth_forwarding.py
```

### Test Coverage

```bash
# Install coverage
pip install coverage

# Run tests with coverage
coverage run -m pytest testing/
coverage report
coverage html  # Generate HTML report
```

## 📋 Test Checklist

Before deploying, ensure all tests pass:

- [ ] Root agent tests (standalone mode)
- [ ] Root agent tests (multi-agent mode)
- [ ] Data analysis agent tests
- [ ] Notification agent tests
- [ ] Approval agent tests
- [ ] Bearer token forwarding tests
- [ ] OAuth context forwarding tests
- [ ] Multi-agent delegation tests
- [ ] Performance tests (response times < 30s)
- [ ] Error handling tests
- [ ] Configuration validation tests

## 🔧 Troubleshooting Tests

### Common Test Issues

#### 1. Port Already in Use

```bash
# Check what's using the port
lsof -i :8001

# Kill the process
kill -9 $(lsof -t -i:8001)

# Or use different ports
export AGENT_PORT="8101"
export DATA_ANALYSIS_PORT="8102"
```

#### 2. Import Errors

```bash
# Ensure PYTHONPATH is set
export PYTHONPATH="${PYTHONPATH}:$(pwd)/src:$(pwd)/testing"

# Or run from project root
cd agent-template
python testing/test_root_agent.py
```

#### 3. Authentication Failures

```bash
# Check OAuth configuration
echo "Client ID: $OAUTH_CLIENT_ID"
echo "Client Secret: $OAUTH_CLIENT_SECRET"

# Use test credentials
export OAUTH_CLIENT_ID="test-client-id"
export OAUTH_CLIENT_SECRET="test-client-secret"
```

#### 4. Agent Connection Issues

```bash
# Verify agents are accessible
curl http://localhost:8001/health
curl http://localhost:8002/health

# Check agent card endpoints
curl http://localhost:8001/.well-known/agent-card.json
```

## 📚 Additional Resources

- [Standalone Setup Guide](../examples/standalone_setup.md)
- [Multi-Agent Setup Guide](../examples/multi_agent_setup.md)
- [Configuration Examples](../examples/configurations/)
- [Troubleshooting Guide](../examples/troubleshooting.md)

## 🤝 Contributing Tests

When adding new functionality:

1. **Add Unit Tests**: Test individual components
2. **Add Integration Tests**: Test component interactions
3. **Update Test Documentation**: Document new test scenarios
4. **Add to CI Pipeline**: Ensure tests run automatically
5. **Test All Scenarios**: Test both standalone and multi-agent modes