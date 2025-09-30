# Multi-Agent Setup Guide

This guide explains how to set up and run the agent-template with remote agents for advanced multi-agent workflows with authentication forwarding.

## 📋 Overview

In multi-agent mode, the agent-template operates as an orchestrating root agent that can delegate tasks to specialized remote agents:

- **Root Agent** (port 8001): Main orchestrator with OAuth/bearer token authentication
- **Data Analysis Agent** (port 8002): Specialized for data analysis and statistical computations
- **Notification Agent** (port 8003): Handles notifications, alerts, and communications
- **Approval Agent** (port 8004): Manages approval workflows and human-in-the-loop processes

All agents support authentication context forwarding via the A2A protocol.

## 🚀 Quick Start

### 1. Prerequisites

Ensure you have the following:
- Python 3.8+
- Google ADK installed and configured
- Multiple available ports (8001-8004)
- Required dependencies installed

### 2. Configuration Setup

#### Step 1: Configure Remote Agents

Create or update `config/remote_agents.yaml`:

```yaml
remote_agents:
  # Data Analysis Agent - Handles complex data processing
  - name: "data_analysis_agent"
    description: "Handles complex data analysis, statistical computations, data visualization, and reporting tasks"
    agent_card_url: "http://localhost:8002/a2a/data_analysis_agent"
    enabled: true

  # Notification Agent - Manages communications and alerts
  - name: "notification_agent"
    description: "Sends notifications, alerts, emails, SMS, and handles all communication tasks"
    agent_card_url: "http://localhost:8003/a2a/notification_agent"
    enabled: true

  # Approval Agent - Handles workflow approvals
  - name: "approval_agent"
    description: "Handles approval workflows, human-in-the-loop processes, and escalation management"
    agent_card_url: "http://localhost:8004/a2a/approval_agent"
    enabled: true
```

#### Step 2: Environment Configuration

Set up environment variables for each agent:

```bash
# Root Agent (port 8001)
export AGENT_NAME="AuthenticatedAgent"
export AGENT_PORT="8001"
export MODEL_NAME="gemini-2.0-flash"

# Data Analysis Agent (port 8002)
export DATA_ANALYSIS_PORT="8002"
export DATA_ANALYSIS_HOST="localhost"

# Notification Agent (port 8003)
export NOTIFICATION_PORT="8003"
export NOTIFICATION_HOST="localhost"

# Approval Agent (port 8004)
export APPROVAL_PORT="8004"
export APPROVAL_HOST="localhost"

# Authentication
export OAUTH_CLIENT_ID="your-oauth-client-id"
export OAUTH_CLIENT_SECRET="your-oauth-client-secret"
export LOG_LEVEL="INFO"
```

### 3. Starting All Agents

#### Method A: Manual Startup (Recommended for Development)

Start each agent in separate terminals:

```bash
# Terminal 1: Start Root Agent
cd agent-template
python src/agent.py

# Terminal 2: Start Data Analysis Agent
cd agent-template
python testing/remote_agents/data_analysis_agent/src/agent.py

# Terminal 3: Start Notification Agent
cd agent-template
python testing/remote_agents/notification_agent/src/agent.py

# Terminal 4: Start Approval Agent
cd agent-template
python testing/remote_agents/approval_agent/src/agent.py
```

#### Method B: Using Screen/Tmux (Background Processes)

```bash
# Start all agents in background using screen
screen -dmS root_agent bash -c 'cd agent-template && python src/agent.py'
screen -dmS data_agent bash -c 'cd agent-template && python testing/remote_agents/data_analysis_agent/src/agent.py'
screen -dmS notify_agent bash -c 'cd agent-template && python testing/remote_agents/notification_agent/src/agent.py'
screen -dmS approval_agent bash -c 'cd agent-template && python testing/remote_agents/approval_agent/src/agent.py'

# List running sessions
screen -ls

# Attach to a session (e.g., to view logs)
screen -r root_agent
```

#### Method C: Docker Compose (Production)

Create `docker-compose.yml`:

```yaml
version: '3.8'
services:
  root-agent:
    build: .
    ports:
      - "8001:8001"
    environment:
      - AGENT_PORT=8001
      - AGENT_NAME=AuthenticatedAgent
    command: python src/agent.py

  data-analysis-agent:
    build: .
    ports:
      - "8002:8002"
    environment:
      - DATA_ANALYSIS_PORT=8002
    command: python testing/remote_agents/data_analysis_agent/src/agent.py

  notification-agent:
    build: .
    ports:
      - "8003:8003"
    environment:
      - NOTIFICATION_PORT=8003
    command: python testing/remote_agents/notification_agent/src/agent.py

  approval-agent:
    build: .
    ports:
      - "8004:8004"
    environment:
      - APPROVAL_PORT=8004
    command: python testing/remote_agents/approval_agent/src/agent.py
```

Then run:
```bash
docker-compose up -d
```

### 4. Verification

#### Check All Agents Are Running

```bash
# Check root agent
curl http://localhost:8001/health

# Check data analysis agent
curl http://localhost:8002/health

# Check notification agent
curl http://localhost:8003/health

# Check approval agent
curl http://localhost:8004/health
```

#### Verify Agent Cards

```bash
# Root agent card
curl http://localhost:8001/.well-known/agent-card.json

# Remote agent cards
curl http://localhost:8002/.well-known/agent-card.json
curl http://localhost:8003/.well-known/agent-card.json
curl http://localhost:8004/.well-known/agent-card.json
```

#### Test Multi-Agent Delegation

```bash
curl -X POST http://localhost:8001/a2a \\
  -H "Content-Type: application/json" \\
  -H "Authorization: Bearer your-test-token" \\
  -d '{
    "jsonrpc": "2.0",
    "id": "test-delegation",
    "method": "message/send",
    "params": {
      "message": {
        "messageId": "test-msg-1",
        "role": "user",
        "parts": [{"text": "Please delegate data analysis of sales data to the data analysis agent and verify authentication forwarding"}]
      }
    }
  }'
```

## 🔧 Advanced Configuration

### Custom Remote Agents

To add your own remote agents:

1. **Create Agent Implementation**:
   ```python
   # my_custom_agent/src/agent.py
   from google.adk.agents import Agent
   from google.adk.a2a.utils.agent_to_a2a import to_a2a

   def create_custom_agent():
       agent = Agent(
           model="gemini-2.0-flash",
           name="custom_agent",
           instruction="Your custom agent instructions...",
           tools=[your_custom_tools]
       )
       return agent

   def create_custom_a2a_app(port=8005):
       agent = create_custom_agent()
       return to_a2a(agent, port=port)
   ```

2. **Add to Configuration**:
   ```yaml
   remote_agents:
     - name: "custom_agent"
       description: "Your custom agent description"
       agent_card_url: "http://localhost:8005/a2a/custom_agent"
       enabled: true
   ```

3. **Start Your Agent**:
   ```bash
   python my_custom_agent/src/agent.py
   ```

### Network Configuration

#### Remote Hosts (Distributed Setup)

For agents running on different machines:

```yaml
remote_agents:
  - name: "data_analysis_agent"
    description: "Remote data analysis service"
    agent_card_url: "http://data-analysis-server:8002/a2a/data_analysis_agent"
    enabled: true

  - name: "notification_agent"
    description: "Remote notification service"
    agent_card_url: "http://notification-server:8003/a2a/notification_agent"
    enabled: true
```

#### Load Balancing

For multiple instances of the same agent type:

```yaml
remote_agents:
  - name: "data_analysis_agent_1"
    description: "Data analysis service - Instance 1"
    agent_card_url: "http://analysis-1:8002/a2a/data_analysis_agent"
    enabled: true

  - name: "data_analysis_agent_2"
    description: "Data analysis service - Instance 2"
    agent_card_url: "http://analysis-2:8002/a2a/data_analysis_agent"
    enabled: true
```

### Security Configuration

#### TLS/HTTPS Setup

For production, use HTTPS for all agent communications:

```yaml
remote_agents:
  - name: "data_analysis_agent"
    description: "Secure data analysis service"
    agent_card_url: "https://analysis.yourdomain.com/a2a/data_analysis_agent"
    enabled: true
    ssl_verify: true
```

#### Authentication Headers

For additional security, configure custom authentication headers:

```yaml
remote_agents:
  - name: "data_analysis_agent"
    description: "Authenticated data analysis service"
    agent_card_url: "https://analysis.yourdomain.com/a2a/data_analysis_agent"
    enabled: true
    auth_headers:
      X-API-Key: "your-api-key"
      X-Service-Token: "service-token"
```

## 🧪 Testing Multi-Agent Setup

### Automated Testing

Run the comprehensive test suite:

```bash
# Test individual remote agents
python testing/test_remote_agents/test_data_analysis_agent.py
python testing/test_remote_agents/test_notification_agent.py
python testing/test_remote_agents/test_approval_agent.py

# Test root agent with multi-agent mode
python testing/test_root_agent.py

# Test end-to-end authentication forwarding
python testing/test_auth_forwarding.py
```

### Manual Testing Workflows

#### 1. Data Analysis Workflow

```bash
curl -X POST http://localhost:8001/a2a \\
  -H "Authorization: Bearer your-token" \\
  -H "Content-Type: application/json" \\
  -d '{
    "jsonrpc": "2.0",
    "id": "data-analysis-test",
    "method": "message/send",
    "params": {
      "message": {
        "messageId": "test-1",
        "role": "user",
        "parts": [{"text": "Please analyze sales_data using trends analysis and provide insights"}]
      }
    }
  }'
```

#### 2. Notification Workflow

```bash
curl -X POST http://localhost:8001/a2a \\
  -H "Authorization: Bearer your-token" \\
  -H "Content-Type: application/json" \\
  -d '{
    "jsonrpc": "2.0",
    "id": "notification-test",
    "method": "message/send",
    "params": {
      "message": {
        "messageId": "test-2",
        "role": "user",
        "parts": [{"text": "Please send an email notification to admin@example.com about the completed analysis"}]
      }
    }
  }'
```

#### 3. Approval Workflow

```bash
curl -X POST http://localhost:8001/a2a \\
  -H "Authorization: Bearer your-token" \\
  -H "Content-Type: application/json" \\
  -d '{
    "jsonrpc": "2.0",
    "id": "approval-test",
    "method": "message/send",
    "params": {
      "message": {
        "messageId": "test-3",
        "role": "user",
        "parts": [{"text": "Please request approval for document DOC-123 from manager@example.com"}]
      }
    }
  }'
```

#### 4. Multi-Step Workflow

```bash
curl -X POST http://localhost:8001/a2a \\
  -H "Authorization: Bearer your-token" \\
  -H "Content-Type: application/json" \\
  -d '{
    "jsonrpc": "2.0",
    "id": "multi-step-test",
    "method": "message/send",
    "params": {
      "message": {
        "messageId": "test-4",
        "role": "user",
        "parts": [{"text": "Please: 1) Analyze sales data, 2) Send summary notification, 3) Request approval for the report"}]
      }
    }
  }'
```

## 📊 Expected Behavior

### Startup Logs

#### Root Agent
```
INFO - Loading remote agents from config/remote_agents.yaml
INFO - Creating remote agent: data_analysis_agent
INFO - Creating remote agent: notification_agent
INFO - Creating remote agent: approval_agent
INFO - Created agent with 3 remote sub-agents
INFO - Starting server on 0.0.0.0:8001
```

#### Remote Agents
```
INFO - Starting Data Analysis Agent on localhost:8002
INFO - Agent Card: http://localhost:8002/.well-known/agent-card.json
INFO - A2A Endpoint: http://localhost:8002/a2a/data_analysis_agent
```

### Agent Capabilities

The root agent will show enhanced instructions:

```
You are an AI assistant with secure OAuth authentication capabilities.

Your primary capabilities:
- Secure OAuth authentication with multiple providers
- Access to authenticated APIs and user data
- Bearer token analysis and forwarding

Remote Agent Delegation:
You can delegate specialized tasks to the following remote agents:
- data_analysis_agent: Handles complex data analysis, statistical computations, data visualization, and reporting tasks
- notification_agent: Sends notifications, alerts, emails, SMS, and handles all communication tasks
- approval_agent: Handles approval workflows, human-in-the-loop processes, and escalation management

When delegating:
1. Choose the most appropriate agent for the task
2. Authentication context will be automatically forwarded
3. Provide clear task instructions to the remote agent
```

## 🔍 Troubleshooting

### Common Issues

#### 1. Remote Agent Connection Failed

**Problem**: Root agent cannot connect to remote agents.

**Diagnostics**:
```bash
# Check if remote agents are running
curl http://localhost:8002/health
curl http://localhost:8003/health
curl http://localhost:8004/health

# Check agent cards are accessible
curl http://localhost:8002/.well-known/agent-card.json
```

**Solutions**:
- Ensure all remote agents are started
- Check port availability: `netstat -ln | grep 800[1-4]`
- Verify agent card URLs in config
- Check firewall settings

#### 2. Authentication Not Forwarded

**Problem**: Remote agents don't receive authentication context.

**Diagnostics**:
```bash
# Test auth forwarding directly
python testing/test_auth_forwarding.py
```

**Solutions**:
- Verify bearer token format
- Check OAuth configuration
- Ensure session state is preserved
- Review agent tool implementations

#### 3. Agent Not Delegating to Remote Agents

**Problem**: Root agent doesn't delegate tasks to remote agents.

**Diagnostics**:
- Check remote_agents.yaml syntax
- Verify all agents are enabled
- Review agent instructions

**Solutions**:
- Ensure agent descriptions are clear and specific
- Check that LLM understands when to delegate
- Verify A2A protocol communication

#### 4. Performance Issues

**Problem**: Slow response times or timeouts.

**Solutions**:
- Increase timeout values in configurations
- Optimize agent instructions for faster delegation decisions
- Consider load balancing for high-traffic scenarios
- Monitor resource usage on all agent hosts

### Monitoring and Logging

#### Enable Debug Logging
```bash
export LOG_LEVEL="DEBUG"
# Restart all agents
```

#### Monitor Agent Health
```bash
# Create a monitoring script
#!/bin/bash
for port in 8001 8002 8003 8004; do
  echo "Checking agent on port $port:"
  curl -s http://localhost:$port/health | jq .
  echo "---"
done
```

#### Log Aggregation

For production, consider using log aggregation:
- **ELK Stack**: Elasticsearch, Logstash, Kibana
- **Prometheus + Grafana**: For metrics and monitoring
- **Centralized logging**: Fluentd or similar

## 🚀 Production Deployment

### Kubernetes Deployment

Example Kubernetes manifests:

```yaml
# k8s/root-agent-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: root-agent
spec:
  replicas: 2
  selector:
    matchLabels:
      app: root-agent
  template:
    metadata:
      labels:
        app: root-agent
    spec:
      containers:
      - name: root-agent
        image: your-registry/agent-template:latest
        ports:
        - containerPort: 8001
        env:
        - name: AGENT_PORT
          value: "8001"
        command: ["python", "src/agent.py"]
---
apiVersion: v1
kind: Service
metadata:
  name: root-agent-service
spec:
  selector:
    app: root-agent
  ports:
  - port: 8001
    targetPort: 8001
  type: LoadBalancer
```

### Cloud Deployment Considerations

- **Load Balancing**: Use cloud load balancers for agent endpoints
- **Service Discovery**: Implement service discovery for dynamic agent registration
- **Auto-scaling**: Configure auto-scaling based on request volume
- **Health Checks**: Implement comprehensive health check endpoints
- **Security**: Use cloud-native security features (VPC, security groups, etc.)

## 📚 Next Steps

1. **Performance Optimization**: Profile and optimize agent response times
2. **Security Hardening**: Implement additional security measures for production
3. **Monitoring**: Set up comprehensive monitoring and alerting
4. **Custom Agents**: Develop domain-specific remote agents for your use case

## 🔗 Related Documentation

- [Standalone Setup Guide](standalone_setup.md)
- [Testing Documentation](../testing/README.md)
- [Troubleshooting Guide](troubleshooting.md)
- [Configuration Reference](configuration_reference.md)
- [Authentication Guide](authentication_guide.md)