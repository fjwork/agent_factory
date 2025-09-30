# Agent Template - Multi-Agent OAuth-Authenticated AI Agent

A **production-ready** template for building Google ADK (Agent Development Kit) agents with OAuth authentication, A2A (Agent-to-Agent) protocol integration, and **optional remote agent orchestration**.

## 🎯 Overview

This template provides a complete foundation for creating OAuth-authenticated AI agents with enterprise-grade security, real API integration, and **optional multi-agent capabilities**. Built on Google ADK with working OAuth flows, authentication patterns, and multi-agent orchestration proven in production.

**Status**: ✅ **PRODUCTION READY** - Full OAuth flows, bearer token forwarding, and multi-agent orchestration working end-to-end.

## ✨ Key Features

### 🔐 Authentication & Security
- **Dual Authentication Support**: Bearer token + OAuth device flow authentication
- **Multi-Provider Support**: Google, Azure AD, Okta, and custom identity providers
- **Enterprise Security**: Token encryption, HTTPS enforcement, JWT validation
- **Authentication Forwarding**: Bearer tokens and OAuth context preserved across agent boundaries

### 🤖 Agent Capabilities
- **Optional Remote Agents**: Seamlessly switch between standalone and multi-agent modes
- **Multi-Agent Orchestration**: Delegate specialized tasks to remote agents with automatic auth forwarding
- **Google ADK Integration**: Native Gemini model integration with tool execution
- **A2A Protocol**: Full Agent-to-Agent protocol with official ADK patterns

### 🏗️ Architecture & Integration
- **Flexible Deployment**: Standalone agent or multi-agent orchestrator based on configuration
- **Real API Integration**: Live data from OAuth provider APIs
- **Token Management**: Automatic refresh, secure storage, lifecycle management
- **Template Structure**: Easy to customize for your specific agent needs

### 🧪 Testing & Quality
- **Comprehensive Testing**: Complete test suite for standalone, multi-agent, and auth forwarding scenarios
- **Modular Test Scripts**: Separate tests for root agent, individual remote agents, and end-to-end workflows
- **Authentication Verification**: Tests bearer token and OAuth context forwarding across agent boundaries
- **Production Documentation**: Complete setup guides, configuration examples, and troubleshooting

## 🏗️ Template Architecture

### Standalone Mode (Default)
```
┌─────────────────────────────────────────────────────────────┐
│                  Your Custom Agent                         │
│                   (Built from Template)                    │
│                                                             │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────┐  │
│  │   Agent Core    │  │  OAuth System   │  │ A2A Server  │  │
│  │  (agent.py)     │  │ (auth/*)        │  │(agent_a2a/*) │  │
│  └─────────────────┘  └─────────────────┘  └─────────────┘  │
│           │                     │                   │       │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────┐  │
│  │ Custom Tools    │  │ Token Storage   │  │  HTTP API   │  │
│  │ (tools/*)       │  │(credential_*)   │  │  Handlers   │  │
│  └─────────────────┘  └─────────────────┘  └─────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### Multi-Agent Mode (Optional)
```
┌─────────────────────────────────────────────────────────────┐
│                    Root Agent (Orchestrator)               │
│                                                             │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────┐  │
│  │   Agent Core    │  │  OAuth System   │  │ A2A Server  │  │
│  │ + Remote Agents │  │ + Auth Forward  │  │+ Agent Cards│  │
│  └─────────┬───────┘  └─────────────────┘  └─────────────┘  │
└───────────┼─────────────────────────────────────────────────┘
            │ A2A + Auth Forwarding
            ▼
┌───────────────────────────────────────────────────────────────┐
│        🔗 Remote Specialized Agents (Optional)               │
│                                                               │
│ ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐   │
│ │ Data Analysis   │ │ Notification    │ │ Approval        │   │
│ │ Agent           │ │ Agent           │ │ Agent           │   │
│ │ (Port 8002)     │ │ (Port 8003)     │ │ (Port 8004)     │   │
│ └─────────────────┘ └─────────────────┘ └─────────────────┘   │
│                                                               │
│ • Statistical Analysis    • Email/SMS/Slack      • Workflow Approvals │
│ • Data Visualization     • Push Notifications    • Human-in-the-Loop  │
│ • Reporting              • Alert Management      • Escalation         │
└───────────────────────────────────────────────────────────────┘
```

## 📁 Template Structure

```
agent-template/
├── src/                               # Core agent implementation
│   ├── agent.py                       # Main entry point - create_agent() function
│   ├── agent_factory/                 # Remote agent management
│   │   ├── __init__.py
│   │   └── remote_agent_factory.py   # RemoteAgentFactory for multi-agent orchestration
│   ├── auth/                          # OAuth authentication system
│   │   ├── oauth_middleware.py        # OAuth middleware for authentication flows
│   │   ├── dual_auth_middleware.py    # Dual authentication (Bearer + OAuth)
│   │   ├── credential_store.py        # Token storage (Memory/File/SecretManager)
│   │   ├── auth_config.py            # Authentication configuration
│   │   └── agent_auth_callback.py    # Authentication context injection
│   ├── agent_a2a/                    # Agent-to-Agent protocol implementation
│   │   ├── server.py                 # AuthenticatedA2AServer class
│   │   ├── handlers.py               # AuthenticatedRequestHandler class
│   │   └── agent_card.py            # AgentCardBuilder class
│   └── tools/                        # Agent tools and capabilities
│       ├── authenticated_tool.py     # AuthenticatedTool base class
│       ├── example_tool.py          # Example tool with OAuth API integration
│       ├── auth_validation_tool.py  # Authentication context validation tool
│       └── examples/                # Additional example tools and patterns
├── config/                           # Configuration files
│   ├── agent_config.yaml           # Agent settings and capabilities
│   ├── oauth_config.yaml           # OAuth provider configuration
│   └── remote_agents.yaml          # Remote agents configuration (optional)
├── deployment/                      # Deployment configurations
│   ├── agent_engine/               # Google Agent Engine deployment
│   ├── cloud_run/                  # Cloud Run deployment
│   ├── docker/                     # Docker configurations
│   └── scripts/                    # Deployment automation scripts
├── docs/                           # Documentation
│   └── setup.md                   # Complete setup guide
├── testing_scripts/               # Testing and validation scripts
│   └── [various test scripts]     # Authentication, A2A, and integration tests
├── .env.example                   # Environment variables template
├── requirements.txt               # Python dependencies
└── README.md                      # This documentation
```

## 🗂️ Folder Descriptions

### `src/` - Core Implementation
**Purpose**: Contains all the agent's source code and business logic

- **`agent.py`**: Main entry point that creates and configures the agent
- **`agent_factory/`**: Manages remote agent connections and orchestration
- **`auth/`**: Complete OAuth authentication system with token management
- **`agent_a2a/`**: Agent-to-Agent protocol implementation for multi-agent communication
- **`tools/`**: Agent capabilities - tools the agent can execute

### `config/` - Configuration
**Purpose**: YAML configuration files for different aspects of the agent

- **`agent_config.yaml`**: Agent metadata, capabilities, and behavior settings
- **`oauth_config.yaml`**: OAuth provider settings (Google, Azure, etc.)
- **`remote_agents.yaml`**: Optional configuration for remote agent orchestration

### `deployment/` - Deployment Options
**Purpose**: Ready-to-use deployment configurations for different platforms

- **`agent_engine/`**: Google Agent Engine deployment files
- **`cloud_run/`**: Google Cloud Run deployment configuration
- **`docker/`**: Docker containerization files
- **`scripts/`**: Automated deployment and setup scripts

### `docs/` - Documentation
**Purpose**: Setup guides and documentation

- **`setup.md`**: Comprehensive setup instructions for the template

### `testing_scripts/` - Testing & Validation
**Purpose**: Scripts to test authentication, A2A communication, and agent functionality

- Contains various test scripts for validating authentication forwarding
- A2A protocol testing
- Integration testing with remote agents

## 🚀 Quick Start

### Choose Your Deployment Mode

The agent-template supports two deployment modes:

#### 🎯 **Standalone Mode** (Default)
Perfect for single-agent scenarios:
- No configuration needed - works out of the box
- Single agent with OAuth authentication
- All tools execute within the main agent
- Ideal for: Simple use cases, development, single-domain tasks

#### 🔗 **Multi-Agent Mode** (Optional)
Advanced multi-agent orchestration:
- Configure `config/remote_agents.yaml` to enable
- Root agent delegates to specialized remote agents
- Authentication automatically forwarded across agents
- Ideal for: Complex workflows, specialized tasks, enterprise scenarios

```bash
# Standalone mode (default)
python src/agent.py
# ✅ Single agent on port 8001

# Multi-agent mode
cp examples/configurations/complete_remote_agents.yaml config/remote_agents.yaml
python src/agent.py                                    # Root agent (port 8001)
python testing/remote_agents/data_analysis_agent/src/agent.py    # Optional (port 8002)
python testing/remote_agents/notification_agent/src/agent.py     # Optional (port 8003)
python testing/remote_agents/approval_agent/src/agent.py         # Optional (port 8004)
# ✅ Multi-agent system with specialized capabilities
```

### 1. Prerequisites

```bash
# Install Python 3.11+ and dependencies
pip install -r requirements.txt

# Set up Google Cloud Authentication
gcloud auth application-default login
export GOOGLE_CLOUD_PROJECT="your-project-id"
```

### 2. OAuth Configuration

#### Google OAuth Setup
1. Go to [Google Cloud Console > Credentials](https://console.cloud.google.com/apis/credentials)
2. Create OAuth 2.0 Client ID (Desktop application)
3. Configure environment variables in `.env`:

```bash
# Update these values in .env
GOOGLE_OAUTH_CLIENT_ID="your-client-id"
GOOGLE_OAUTH_CLIENT_SECRET="your-client-secret"
GOOGLE_CLOUD_PROJECT="your-project-id"
```

### 3. Customize Your Agent

#### Step 1: Update Agent Configuration
Edit `config/agent_config.yaml`:
```yaml
agent:
  name: "YourAgentName"
  description: "Description of your agent's purpose"

skills:
  - id: "your_skill"
    name: "Your Skill Name"
    description: "What your agent can do"
    examples:
      - "Example request 1"
      - "Example request 2"
```

#### Step 2: Create Your Custom Tools
Replace `src/tools/example_tool.py` with your custom tools:

```python
from .authenticated_tool import AuthenticatedTool

class YourCustomTool(AuthenticatedTool):
    def __init__(self):
        super().__init__(
            name="your_tool",
            description="Your tool description"
        )

    async def execute_authenticated(self, user_context, **kwargs):
        # Your tool logic here
        user_info = await self.fetch_real_user_info(user_context)
        # Process and return results
        return {"success": True, "data": "your_results"}
```

#### Step 3: Update Agent Instructions
Edit `src/agent.py` function `create_agent()`:
```python
instruction=f"""
You are {agent_name}, specialized in [YOUR DOMAIN].

Your capabilities:
- [Capability 1]
- [Capability 2]
- [Capability 3]

Available tools:
- your_tool: [Description]
"""
```

### 4. Run Your Agent

```bash
# Start your customized agent
cd src
python agent.py

# Agent starts on http://localhost:8001
# Agent card: http://localhost:8001/.well-known/agent-card.json
```

### 5. Test OAuth Flow

```bash
# Run the OAuth test client
python oauth_test_client.py

# Follow the device flow instructions:
# 1. Visit the provided Google URL
# 2. Enter the device code
# 3. Authorize the application
# 4. Test your custom tools
```

## 🔐 Dual Authentication Guide

This template supports **two authentication patterns** that can work together:

### Pattern 1: Bearer Token Authentication (New)
For pre-authenticated requests from web apps or orchestrator agents:

```bash
# Example: Bearer token from web app
curl -X POST http://localhost:8001/ \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..." \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": "1",
    "method": "message/send",
    "params": {
      "message": {
        "messageId": "msg-1",
        "role": "user",
        "parts": [{"text": "Hello from web app"}]
      }
    }
  }'
```

### Pattern 2: OAuth Device Flow (Existing)
For interactive user authentication:

```bash
# Step 1: Initiate OAuth flow
curl -X POST http://localhost:8001/auth/initiate \
  -H "Content-Type: application/json" \
  -d '{"user_id": "user@example.com", "provider": "google"}'

# Step 2: User completes OAuth in browser
# Step 3: Send authenticated A2A request
curl -X POST http://localhost:8001/ \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": "1",
    "method": "message/send",
    "params": {
      "message": {
        "messageId": "msg-2",
        "role": "user",
        "parts": [{"text": "Hello from OAuth user"}]
      }
    },
    "user_id": "user@example.com"
  }'
```

### Testing Bearer Token Validation

Configure bearer token validation mode in `.env`:

```bash
# Always accept bearer tokens (testing)
BEARER_TOKEN_VALIDATION=valid

# Always reject bearer tokens (testing)
BEARER_TOKEN_VALIDATION=invalid

# Validate as JWT (production)
BEARER_TOKEN_VALIDATION=jwt
```

### Authentication Priority

The system uses this priority order:
1. **Bearer token** (from `Authorization: Bearer <token>` header)
2. **OAuth session** (existing user with valid tokens)
3. **Device flow initiation** (for new users)

### Dual Authentication Status

Check authentication capabilities:

```bash
curl http://localhost:8001/auth/dual-status
```

Response includes:
- Supported authentication methods
- Current authentication status
- Bearer token validation mode
- Environment testing configuration

## 🔧 Customization Guide

### Adding New OAuth Providers

1. **Update OAuth Config** (`config/oauth_config.yaml`):
```yaml
providers:
  your_provider:
    client_id: "${YOUR_PROVIDER_CLIENT_ID}"
    client_secret: "${YOUR_PROVIDER_CLIENT_SECRET}"
    authorization_url: "https://your-provider.com/oauth/authorize"
    token_url: "https://your-provider.com/oauth/token"
    userinfo_url: "https://your-provider.com/api/user"
```

2. **Add Provider Support** in `src/tools/authenticated_tool.py`:
```python
async def _fetch_your_provider_user_info(self, access_token: str) -> Dict[str, Any]:
    # Implement your provider's userinfo API call
    pass
```

### Creating Domain-Specific Tools

1. **Extend AuthenticatedTool**:
```python
class MyDomainTool(AuthenticatedTool):
    async def execute_authenticated(self, user_context, action, **kwargs):
        # Your domain-specific logic
        api_data = await self._call_external_api(user_context["token"])
        return self._format_response(api_data)

    async def _call_external_api(self, token):
        # Make authenticated API calls to your services
        pass
```

2. **Register Tools** in `src/agent.py`:
```python
# Create your tools
my_tool = MyDomainTool()
my_function_tool = FunctionTool(my_tool.execute_with_context)

# Add to agent
agent = Agent(
    tools=[my_function_tool],
    # ... other config
)
```

### Environment-Specific Configuration

Create environment-specific `.env` files:
- `.env.development` - Development settings
- `.env.staging` - Staging settings
- `.env.production` - Production settings

## 🛡️ Security Features

### Token Security
- **Encryption**: AES-256 encryption for file-based storage
- **Lifecycle**: Automatic token refresh using refresh tokens
- **Validation**: JWT signature verification for ID tokens
- **Isolation**: Per-user token isolation and session management

### Authentication Methods
- **Bearer Tokens**: `Authorization: Bearer <token>` header support
- **API Keys**: `X-API-Key` header for service accounts
- **Basic Auth**: Client credentials for machine-to-machine
- **JWT Validation**: ID token signature verification

## 📊 API Endpoints

### A2A Protocol
| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/` | POST | A2A messages with your custom tools |
| `/.well-known/agent-card.json` | GET | Public agent card |

### OAuth Authentication
| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/auth/initiate` | POST | Start OAuth flow |
| `/auth/complete` | POST | Complete OAuth flow |
| `/auth/status` | GET | Check auth status |

### Health & Monitoring
| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/health` | GET | Service health check |

## 🔗 Multi-Agent Capabilities

### Remote Agent Overview

The template includes three sample remote agents that demonstrate different specialization patterns:

#### 📊 Data Analysis Agent (Port 8002)
Specialized for data processing and analytics:
- **Capabilities**: Statistical analysis, data visualization, trend analysis, forecasting
- **Use Cases**: Sales data analysis, user behavior analytics, custom reporting
- **Authentication**: Receives and verifies bearer tokens and OAuth context
- **Tools**: `DataAnalysisTool` with mock datasets and analysis types

#### 🔔 Notification Agent (Port 8003)
Handles all communication and alerting:
- **Capabilities**: Multi-channel notifications (email, SMS, Slack, push)
- **Use Cases**: Alert management, notification delivery, communication workflows
- **Authentication**: Auth context verification for user-specific notifications
- **Tools**: `NotificationTool` with mock provider integration

#### ✋ Approval Agent (Port 8004)
Manages workflows and human-in-the-loop processes:
- **Capabilities**: Approval workflows, escalation management, human oversight
- **Use Cases**: Document approvals, expense workflows, access requests
- **Authentication**: Auth context for approval authority verification
- **Tools**: `ApprovalTool` with workflow state management

### Multi-Agent Workflow Example

```bash
# User request with authentication
curl -X POST http://localhost:8001/a2a \
  -H "Authorization: Bearer your-token" \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": "workflow-1",
    "method": "message/send",
    "params": {
      "message": {
        "messageId": "msg-1",
        "role": "user",
        "parts": [{
          "text": "Please analyze our Q4 sales data, send a summary to the team, and request approval for the budget increase"
        }]
      }
    }
  }'

# Root agent automatically:
# 1. Delegates analysis to Data Analysis Agent
# 2. Forwards authentication context via A2A
# 3. Delegates notification to Notification Agent
# 4. Delegates approval to Approval Agent
# 5. Coordinates the complete workflow
```

### Authentication Forwarding

All authentication information is automatically forwarded to remote agents:

- **Bearer Tokens**: Preserved in session state and forwarded via A2A protocol
- **OAuth Context**: User information, provider details, and tokens maintained
- **Session State**: Complete authentication context available to remote agents
- **Verification**: Each remote agent can verify and extract auth information

```python
# Remote agents automatically receive auth context
def _extract_auth_info(self, state_dict: Dict[str, Any]) -> Dict[str, Any]:
    # Check for OAuth context
    if state_dict.get("oauth_authenticated"):
        return {
            "authenticated": True,
            "auth_type": "oauth",
            "user_id": state_dict.get("oauth_user_id"),
            "oauth_context": {...}
        }
    # Check for bearer token
    elif state_dict.get("oauth_token"):
        return {
            "authenticated": True,
            "auth_type": "bearer",
            "token_present": True
        }
```

### Configuration Management

#### Enable Multi-Agent Mode

```yaml
# config/remote_agents.yaml
remote_agents:
  - name: "data_analysis_agent"
    description: "Handles complex data analysis and reporting"
    agent_card_url: "http://localhost:8002/a2a/data_analysis_agent"
    enabled: true

  - name: "notification_agent"
    description: "Manages notifications and communications"
    agent_card_url: "http://localhost:8003/a2a/notification_agent"
    enabled: true

  - name: "approval_agent"
    description: "Handles approval workflows"
    agent_card_url: "http://localhost:8004/a2a/approval_agent"
    enabled: false  # Can disable individual agents
```

#### Example Configurations

- **`examples/configurations/minimal_remote_agents.yaml`**: Single data analysis agent
- **`examples/configurations/complete_remote_agents.yaml`**: All three sample agents
- **`examples/configurations/development_remote_agents.yaml`**: Development/testing setup
- **`examples/configurations/production_remote_agents.yaml`**: Production deployment

### Custom Remote Agents

Create your own specialized agents:

```python
# my_custom_agent/src/agent.py
from google.adk.agents import Agent
from google.adk.a2a.utils.agent_to_a2a import to_a2a

def create_custom_agent():
    agent = Agent(
        model="gemini-2.0-flash",
        name="my_custom_agent",
        instruction="Your custom agent instructions...",
        tools=[your_custom_tools]
    )
    return agent

def create_custom_a2a_app(port=8005):
    agent = create_custom_agent()
    return to_a2a(agent, port=port)

# Add to config/remote_agents.yaml
# - name: "my_custom_agent"
#   description: "Your custom functionality"
#   agent_card_url: "http://localhost:8005/a2a/my_custom_agent"
#   enabled: true
```

## 🧪 Testing

### Multi-Agent Testing Framework

The template includes comprehensive testing for both standalone and multi-agent modes:

#### Root Agent Tests
```bash
# Test both standalone and multi-agent modes
python testing/test_root_agent.py
```

#### Individual Remote Agent Tests
```bash
# Test each remote agent independently
python testing/test_remote_agents/test_data_analysis_agent.py
python testing/test_remote_agents/test_notification_agent.py
python testing/test_remote_agents/test_approval_agent.py
```

#### End-to-End Authentication Forwarding Tests
```bash
# Start root agent first
python src/agent.py

# Test complete auth forwarding workflows
python testing/test_auth_forwarding.py
```

### Bearer Token Forwarding Test

The template includes comprehensive testing for bearer token forwarding functionality:

#### Quick Bearer Token Test

```bash
# 1. Set up the test environment
./setup_bearer_token_test.sh

# 2. Start the main agent (Terminal 1)
source venv/bin/activate && python3 src/agent.py

# 3. Start the remote test agent (Terminal 2)
source venv/bin/activate && python3 test_remote_agent.py

# 4. Run comprehensive bearer token test (Terminal 3)
source venv/bin/activate && python3 bearer_token_test_client.py
```

#### What the Bearer Token Test Validates

1. **✅ Health Checks**: Both main and remote agents are running
2. **✅ Dual Auth Status**: Bearer token + OAuth authentication is enabled
3. **✅ Token to Tools**: Bearer tokens are forwarded to agent tools
4. **✅ Token to Remote Agents**: Bearer tokens are forwarded via A2A protocol
5. **✅ Invalid Token Handling**: Proper 401 responses for unauthenticated requests

#### Test Results Example

```bash
📊 TEST RESULTS
🎯 Overall Success: True
📈 Success Rate: 100.0%
✅ Passed Tests: 5
❌ Failed Tests: 0

📋 Test Details:
  ✅ PASS health_checks
  ✅ PASS dual_auth_status
  ✅ PASS token_to_tools
  ✅ PASS token_to_remote_agent
  ✅ PASS invalid_token_handling
```

#### Manual Bearer Token Testing

```bash
# Test bearer token with the built-in test tool
curl -X POST http://localhost:8001/ \
  -H "Authorization: Bearer test-token-123" \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": "test-1",
    "method": "message/send",
    "params": {
      "message": {
        "messageId": "test-msg-1",
        "role": "user",
        "parts": [{"text": "Please use the bearer_token_print_tool to analyze my bearer token"}]
      }
    }
  }'
```

### OAuth Testing

#### Using the Test Client

```python
# oauth_test_client.py
client = AgentTestClient("http://localhost:8001")

# Test OAuth flow
auth_data = await client.initiate_oauth("user@example.com")
# User completes OAuth in browser

# Test your custom tools
response = await client.send_authenticated_message(
    "Use my custom tool",
    "user@example.com"
)
```

### Manual Testing

```bash
# Test health
curl http://localhost:8001/health

# Test OAuth initiation
curl -X POST http://localhost:8001/auth/initiate \
  -H "Content-Type: application/json" \
  -d '{"user_id": "test@example.com", "provider": "google"}'

# Test agent card
curl http://localhost:8001/.well-known/agent-card.json
```

## 🚀 Deployment

### Local Development
```bash
# Set environment variables
export GOOGLE_OAUTH_CLIENT_ID="your-client-id"
export GOOGLE_OAUTH_CLIENT_SECRET="your-client-secret"

# Run agent
python src/agent.py
```

### Cloud Run Deployment
```bash
# Build and deploy
gcloud run deploy your-agent \
  --source . \
  --set-env-vars GOOGLE_OAUTH_CLIENT_ID=your-client-id \
  --set-env-vars GOOGLE_OAUTH_CLIENT_SECRET=your-client-secret \
  --port 8001
```

### Vertex AI Agent Engine
```bash
# Deploy to Agent Engine
# Configure agent.yaml with your OAuth credentials
# Deploy via Vertex AI Console or API
```

## 🔍 Troubleshooting

### Common Issues

#### "User authentication required" Error
- **Check**: OAuth client ID/secret configuration in `.env`
- **Verify**: User has completed OAuth flow
- **Debug**: Enable `LOG_LEVEL=DEBUG` to see authentication flow

#### OAuth Flow Failure
- **Check**: OAuth client ID/secret configuration
- **Verify**: Network access to OAuth provider endpoints
- **Debug**: Check logs for specific error messages

#### Token Storage Issues
- **File Storage**: Check file permissions in token storage directory
- **Secret Manager**: Verify Google Cloud credentials and permissions
- **Memory**: Tokens lost on restart (expected for memory storage)

### Debug Logging
```python
# Enable detailed OAuth flow logging
import logging
logging.getLogger('auth.oauth_middleware').setLevel(logging.DEBUG)
logging.getLogger('agent_a2a.handlers').setLevel(logging.DEBUG)
```

## 📋 Template Checklist

### Core Setup
- ✅ **OAuth Configuration**: Update client ID/secret in `.env`
- ✅ **Agent Details**: Customize name, description in `config/agent_config.yaml`
- ✅ **Custom Tools**: Replace `example_tool.py` with your tools
- ✅ **Agent Instructions**: Update agent behavior in `src/agent.py`
- ✅ **Skills Definition**: Define your agent's capabilities
- ✅ **Provider Configuration**: Add any additional OAuth providers
- ✅ **Environment Setup**: Configure for your deployment environment

### Multi-Agent Setup (Optional)
- ✅ **Deployment Mode**: Choose standalone or multi-agent mode
- ✅ **Remote Agents Configuration**: Configure `config/remote_agents.yaml` if using multi-agent mode
- ✅ **Custom Remote Agents**: Create domain-specific remote agents if needed
- ✅ **Authentication Forwarding**: Verify auth context forwarding to remote agents
- ✅ **Multi-Agent Testing**: Test complete workflows across agents

### Testing & Validation
- ✅ **Standalone Testing**: Run `python testing/test_root_agent.py`
- ✅ **Multi-Agent Testing**: Run individual remote agent tests if applicable
- ✅ **Bearer Token Testing**: Test authentication forwarding across agents
- ✅ **OAuth Testing**: Verify OAuth flow and tool execution
- ✅ **End-to-End Testing**: Run `python testing/test_auth_forwarding.py`

### Documentation & Deployment
- ✅ **Documentation**: Update README with your agent's specifics
- ✅ **Configuration Examples**: Set up environment-specific configs
- ✅ **Deployment Planning**: Choose deployment strategy (local, cloud, containerized)
- ✅ **Monitoring Setup**: Configure logging and health checks

## 🔧 Advanced Configuration

### Custom Authentication Flows
```python
# Add custom auth flow in oauth_middleware.py
async def custom_auth_flow(self, user_id: str, custom_params: dict):
    # Implement your custom authentication logic
    pass
```

### External API Integration
```python
# In your custom tool
async def call_external_api(self, user_context):
    token = user_context["token"]
    headers = {"Authorization": f"Bearer {token}"}
    # Make authenticated API calls
```

### Multi-Tenant Support
```python
# Configure tenant-specific OAuth providers
# Add tenant context to user_context
# Implement tenant-specific tool behavior
```

## 📖 Additional Resources

### Setup and Configuration Guides
- **[Standalone Setup Guide](examples/standalone_setup.md)**: Complete setup for single-agent deployment
- **[Multi-Agent Setup Guide](examples/multi_agent_setup.md)**: Advanced multi-agent orchestration setup
- **[Configuration Examples](examples/configurations/)**: Environment-specific configuration templates
- **[Troubleshooting Guide](examples/troubleshooting.md)**: Comprehensive problem resolution guide

### Testing and Development
- **[Testing Documentation](testing/README.md)**: Complete testing framework documentation
- **[Implementation Strategy](IMPLEMENTATION_STRATEGY.md)**: Detailed implementation progress and architecture

### External Documentation
- **Google ADK Documentation**: [Google ADK Guide](https://cloud.google.com/vertex-ai/generative-ai/docs/agent-development-kit)
- **A2A Protocol Specification**: [Agent-to-Agent Protocol](https://docs.a2a.ai/)
- **OAuth 2.0 Device Flow**: [RFC 8628](https://datatracker.ietf.org/doc/html/rfc8628)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Implement changes with tests
4. Update documentation
5. Submit pull request

## 📝 License

This project is licensed under the Apache 2.0 License - see the LICENSE file for details.

---

**Agent Template** - Production-ready foundation for OAuth-authenticated AI agents 🚀