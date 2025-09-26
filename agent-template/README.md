# Agent Template - OAuth-Authenticated AI Agent

A **production-ready** template for building Google ADK (Agent Development Kit) agents with OAuth authentication and A2A (Agent-to-Agent) protocol integration.

## 🎯 Overview

This template provides a complete foundation for creating OAuth-authenticated AI agents with enterprise-grade security and real API integration. Built on Google ADK with working OAuth flows and authentication patterns proven in production.

**Status**: ✅ **PRODUCTION READY** - Full OAuth flows working end-to-end with live API integration.

## ✨ Key Features

- **🔐 Dual Authentication Support**: Bearer token + OAuth device flow authentication
- **🌐 Multi-Provider Support**: Google, Azure AD, Okta, and custom identity providers
- **🛡️ Enterprise Security**: Token encryption, HTTPS enforcement, JWT validation
- **📡 A2A Protocol**: Full Agent-to-Agent protocol with authentication forwarding
- **🤖 Google ADK Integration**: Native Gemini model integration with tool execution
- **📊 Real API Integration**: Live data from OAuth provider APIs
- **🔄 Token Management**: Automatic refresh, secure storage, lifecycle management
- **📋 Template Structure**: Easy to customize for your specific agent needs
- **🔀 Bearer Token Support**: Accept pre-authenticated tokens from web apps/orchestrators

## 🏗️ Template Architecture

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

## 📁 Project Structure

```
agent-template/
├── src/
│   ├── agent.py                          # Main entry point - create_agent()
│   ├── auth/                             # OAuth authentication system
│   │   ├── oauth_middleware.py           # OAuthMiddleware class
│   │   ├── credential_store.py           # Token storage (Memory/File/SecretManager)
│   │   └── auth_config.py               # Configuration management
│   ├── agent_a2a/                       # A2A protocol implementation
│   │   ├── server.py                    # AuthenticatedA2AServer class
│   │   ├── handlers.py                  # AuthenticatedRequestHandler class
│   │   └── agent_card.py               # AgentCardBuilder class
│   └── tools/                           # Agent tools
│       ├── authenticated_tool.py        # AuthenticatedTool base class
│       ├── example_tool.py             # ExampleTool implementation
│       └── examples/                   # Additional example tools
├── config/                              # Configuration files
│   ├── agent_config.yaml              # Agent settings and capabilities
│   └── oauth_config.yaml              # OAuth provider configuration
├── oauth_test_client.py                # OAuth test client
└── README.md                           # This file
```

## 🚀 Quick Start

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
        "role": "user",
        "content": [{"text": "Hello from web app"}]
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
        "role": "user",
        "content": [{"text": "Hello from OAuth user"}]
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

## 🧪 Testing

### Using the Test Client

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

When creating your agent from this template:

- ✅ **OAuth Configuration**: Update client ID/secret in `.env`
- ✅ **Agent Details**: Customize name, description in `config/agent_config.yaml`
- ✅ **Custom Tools**: Replace `example_tool.py` with your tools
- ✅ **Agent Instructions**: Update agent behavior in `src/agent.py`
- ✅ **Skills Definition**: Define your agent's capabilities
- ✅ **Provider Configuration**: Add any additional OAuth providers
- ✅ **Environment Setup**: Configure for your deployment environment
- ✅ **Testing**: Verify OAuth flow and tool execution
- ✅ **Documentation**: Update README with your agent's specifics

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