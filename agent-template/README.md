# ADK Agent Template with OAuth Authentication

A comprehensive template for building Google ADK (Agent Development Kit) agents with OAuth authentication and A2A (Agent-to-Agent) protocol integration.

## 🚀 Features

- **OAuth Integration**: Support for multiple OAuth providers (Google, Azure, Okta, custom)
- **Multiple OAuth Flows**: Device Flow, Authorization Code, Client Credentials
- **Secure Token Storage**: Memory, file-based, or Google Cloud Secret Manager
- **A2A Protocol**: Full Agent-to-Agent protocol implementation with authentication
- **Dual Deployment**: Support for both Cloud Run and Vertex AI Agent Engine
- **Environment Configuration**: Environment-specific settings and overrides
- **Security**: Proper authentication, authorization, and credential management

## 📁 Project Structure

```
agent-template/
├── src/
│   ├── auth/                         # Authentication components
│   │   ├── auth_config.py            # Configuration management
│   │   ├── oauth_middleware.py       # OAuth flow implementation
│   │   └── credential_store.py       # Secure token storage
│   ├── agent_a2a/                    # A2A protocol components
│   │   ├── agent_card.py             # Agent card generation
│   │   ├── server.py                 # A2A server implementation
│   │   └── handlers.py               # Authenticated request handlers
│   ├── tools/                        # Agent tools
│   │   ├── authenticated_tool.py     # Base authenticated tool class
│   │   └── examples/                 # Example tool implementations
│   │       ├── profile_example_tool.py  # Profile retrieval example
│   │       └── api_example_tool.py      # API integration example
│   └── agent.py                      # Main agent implementation
├── config/                       # Configuration files
│   ├── agent_config.yaml         # Agent settings
│   ├── oauth_config.yaml         # OAuth provider settings
│   └── deployment_config.yaml    # Deployment configuration
├── deployment/                   # Deployment scripts and configs
│   ├── cloud_run/               # Cloud Run deployment
│   ├── agent_engine/            # Agent Engine deployment
│   ├── docker/                  # Container configuration
│   └── scripts/                 # Setup and utility scripts
├── oauth_test_client.py          # OAuth flow test client
└── docs/                        # Documentation
```

## 🛠 Quick Start

### 1. Initial Setup

Run the setup script to configure your environment:

```bash
# Basic setup
./deployment/scripts/setup.sh

# Development setup (includes dev dependencies)
./deployment/scripts/setup.sh --dev

# Specify project and location
./deployment/scripts/setup.sh --project YOUR_PROJECT_ID --location us-central1
```

### 2. Configure OAuth

1. Go to [Google Cloud Console > APIs & Services > Credentials](https://console.cloud.google.com/apis/credentials)
2. Create an OAuth 2.0 Client ID for a Desktop application
3. Set environment variables or store in Secret Manager:

```bash
export GOOGLE_OAUTH_CLIENT_ID="your-client-id"
export GOOGLE_OAUTH_CLIENT_SECRET="your-client-secret"
```

### 3. Customize Configuration

Edit the configuration files in the `config/` directory:

- `agent_config.yaml` - Agent behavior and capabilities
- `oauth_config.yaml` - OAuth providers and settings
- `deployment_config.yaml` - Deployment parameters

### 4. Deploy

#### Deploy to Cloud Run:
```bash
python deployment/cloud_run/deploy.py --environment production
```

#### Deploy to Agent Engine:
```bash
python deployment/agent_engine/deploy.py --action create --environment production
```

## 🔧 Configuration

### Agent Configuration (`config/agent_config.yaml`)

```yaml
agent:
  name: "${AGENT_NAME:MyAgent}"
  version: "${AGENT_VERSION:1.0.0}"
  description: "${AGENT_DESCRIPTION:A configurable ADK agent with OAuth authentication}"

  model:
    provider: "${MODEL_PROVIDER:gemini}"
    name: "${MODEL_NAME:gemini-2.0-flash}"
    use_vertex_ai: "${USE_VERTEX_AI:true}"

  capabilities:
    streaming: true
    authenticated_extended_card: true

skills:
  - id: "authenticated_api_call"
    name: "Authenticated API Call"
    description: "Makes authenticated API calls using user credentials"
    tags: ["api", "authentication", "secure"]
```

### OAuth Configuration (`config/oauth_config.yaml`)

```yaml
oauth:
  default_provider: "${OAUTH_DEFAULT_PROVIDER:google}"
  flow_type: "${OAUTH_FLOW_TYPE:device_flow}"
  scopes: "${OAUTH_SCOPES:openid profile email}"

providers:
  google:
    client_id: "${GOOGLE_OAUTH_CLIENT_ID}"
    client_secret: "${GOOGLE_OAUTH_CLIENT_SECRET}"
    authorization_url: "https://accounts.google.com/o/oauth2/auth"
    token_url: "https://oauth2.googleapis.com/token"
    device_authorization_url: "https://oauth2.googleapis.com/device/code"
    userinfo_url: "https://www.googleapis.com/oauth2/v3/userinfo"
```

### Environment Variables

Key environment variables you can set:

```bash
# Google Cloud
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_CLOUD_LOCATION=us-central1

# OAuth
GOOGLE_OAUTH_CLIENT_ID=your-client-id
GOOGLE_OAUTH_CLIENT_SECRET=your-client-secret
OAUTH_DEFAULT_PROVIDER=google
OAUTH_FLOW_TYPE=device_flow

# Agent
AGENT_NAME=MyAgent
MODEL_NAME=gemini-2.0-flash
TOKEN_STORAGE_TYPE=secret_manager

# Security
OAUTH_REQUIRE_HTTPS=true
```

## 🔐 Authentication Flows

### Device Flow (Recommended for CLI/Desktop)

1. User requests authentication
2. Agent provides verification URL and code
3. User visits URL and enters code
4. Agent polls for completion
5. Tokens stored securely

### Authorization Code Flow (Web Applications)

1. User redirected to OAuth provider
2. User authorizes application
3. Provider redirects with authorization code
4. Agent exchanges code for tokens

### Client Credentials Flow (Service-to-Service)

1. Agent authenticates with client credentials
2. Receives access token for API calls
3. No user interaction required

## 🛡 Security Features

- **Secure Token Storage**: Choose between memory, encrypted files, or Google Cloud Secret Manager
- **Token Lifecycle Management**: Automatic refresh and expiration handling
- **A2A Authentication**: Multiple security schemes (OAuth2, Bearer, API Key)
- **Per-User Isolation**: User credentials are isolated and encrypted
- **HTTPS Enforcement**: Configurable HTTPS requirements
- **JWT Validation**: Support for JWT token validation

## 🚀 Deployment Options

### Cloud Run

- Serverless containerized deployment
- Auto-scaling based on demand
- Cost-effective for variable workloads
- Full HTTP endpoint exposure

```bash
# Deploy with automatic image building
python deployment/cloud_run/deploy.py

# Deploy using existing image
python deployment/cloud_run/deploy.py --no-build

# Deploy to specific environment
python deployment/cloud_run/deploy.py --environment production
```

### Vertex AI Agent Engine

- Managed agent runtime
- Integrated with Google Cloud AI services
- Enhanced monitoring and observability
- Native Gemini model integration

```bash
# Create new agent
python deployment/agent_engine/deploy.py --action create

# Update existing agent
python deployment/agent_engine/deploy.py --action update --resource-id AGENT_ID

# Test deployed agent
python deployment/agent_engine/deploy.py --action test --resource-id AGENT_ID
```

## 🔧 Development

### Running Locally

1. Install dependencies:
```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt  # For development
```

2. Set up environment:
```bash
cp .env.example .env
# Edit .env with your settings
```

3. Run the agent:
```bash
python src/agent.py
```

### Testing OAuth Authentication

#### Using the Test Client (Recommended)

The template includes a comprehensive test client for validating OAuth flows:

```bash
# Run complete test suite
python oauth_test_client.py --user-id test@example.com

# Test specific components
python oauth_test_client.py --test oauth --user-id test@example.com
python oauth_test_client.py --test tools --user-id test@example.com
python oauth_test_client.py --test health

# Test with different agent URL
python oauth_test_client.py --agent-url http://localhost:8001 --user-id test@example.com

# Enable verbose logging
python oauth_test_client.py --verbose --user-id test@example.com
```

The test client will:
1. Check initial authentication status
2. Initiate OAuth flow if needed
3. Guide you through browser authentication
4. Test authenticated tool execution
5. Validate all endpoints

#### Manual Testing with curl

```bash
# Initiate authentication
curl -X POST http://localhost:8000/auth/initiate \
  -H "Content-Type: application/json" \
  -d '{"user_id": "test-user", "provider": "google"}'

# Check authentication status
curl "http://localhost:8000/auth/status?user_id=test-user"

# Test agent with authentication
curl -X POST http://localhost:8000/ \
  -H "Content-Type: application/json" \
  -d '{"user_id": "test-user", "session_id": "test-session", "message": "Hello!"}'
```

## 📖 API Documentation

### A2A Endpoints

- `GET /.well-known/agent-card.json` - Public agent card
- `POST /` - A2A protocol messages (requires auth)
- `GET /agent/authenticatedExtendedCard` - Extended card (requires auth)

### Authentication Endpoints

- `POST /auth/initiate` - Start OAuth flow
- `POST /auth/complete` - Complete OAuth flow
- `GET /auth/status` - Check auth status
- `POST /auth/revoke` - Revoke tokens

### Health Check

- `GET /health` - Service health status

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📝 License

This template is provided under the Apache 2.0 License. See LICENSE file for details.

## 🆘 Support

- **Documentation**: See `docs/` directory for detailed guides
- **Issues**: Report issues on the project repository
- **Examples**: Check `src/tools/examples/` for implementation examples

## 🔧 Key Features & Improvements

This template provides a **production-ready** foundation for OAuth-authenticated agents with several critical improvements:

### ✅ **Fixed OAuth Integration**
- **Critical Bug Fix**: OAuth tokens now properly included in user context
- **Session State Storage**: OAuth context stored in ADK session state for tool access
- **Fallback Registry**: Global OAuth registry for robust context access
- **Real API Integration**: Live calls to OAuth provider APIs (Google UserInfo, etc.)

### 🛠️ **Enhanced Tool Development**
- **Dual Execution Methods**: Both `execute_authenticated()` and `execute_with_context()`
- **ADK Integration**: Proper `FunctionTool` registration with session state access
- **Example Tools**: Ready-to-use profile and API integration examples
- **Error Handling**: Comprehensive error handling and graceful degradation

### 🔐 **Robust Authentication**
- **Multiple Auth Schemes**: Bearer tokens, API keys, Basic auth, JWT validation
- **Token Management**: Automatic refresh, secure storage, lifecycle management
- **Provider Support**: Google, Azure, Okta, and custom OAuth providers
- **Security**: HTTPS enforcement, token encryption, scope validation

### 🧪 **Comprehensive Testing**
- **Test Client**: Complete OAuth flow validation tool (`oauth_test_client.py`)
- **End-to-End Testing**: Automated testing of all authentication flows
- **Debug Support**: Detailed logging and troubleshooting capabilities

### 📊 **Developer Experience**
- **Clear Documentation**: Step-by-step setup and usage instructions
- **Example Implementations**: Profile and API tools as templates
- **Configuration Management**: Environment-specific settings and overrides
- **Deployment Ready**: Cloud Run and Agent Engine deployment scripts

## 🔄 Migration from Existing Agents

To migrate an existing ADK agent to use this template:

1. Copy your agent logic to `src/agent.py`
2. Update tool registration to use `tool.execute_with_context` instead of `tool.execute_authenticated`
3. Inherit from `AuthenticatedTool` and implement `execute_authenticated()` method
4. Update configuration files with your OAuth settings
5. Test authentication flows using the provided test client
6. Update deployment scripts with your specific requirements