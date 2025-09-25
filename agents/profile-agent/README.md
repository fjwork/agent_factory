# Profile Agent - OAuth-Authenticated AI Agent

A **production-ready** Google ADK (Agent Development Kit) agent that securely retrieves user profile information through OAuth authentication and the A2A (Agent-to-Agent) protocol.

## 🎯 Overview

The Profile Agent demonstrates enterprise-grade OAuth integration with AI agents, providing secure access to user profile data from identity providers like Google, Azure, and Okta. Built on Google ADK with complete A2A protocol support and real-time API integration.

**Status**: ✅ **PRODUCTION READY** - Full OAuth flows working end-to-end with live Google API integration.

## ✨ Key Features

- **🔐 Complete OAuth Integration**: Device Flow, Authorization Code, and Client Credentials flows
- **🌐 Multi-Provider Support**: Google, Azure AD, Okta, and custom identity providers
- **🛡️ Enterprise Security**: Token encryption, HTTPS enforcement, JWT validation
- **📡 A2A Protocol**: Full Agent-to-Agent protocol with authentication
- **🤖 Google ADK Integration**: Native Gemini model integration with tool execution
- **📊 Real API Integration**: Live profile data from Google UserInfo API
- **🔄 Token Management**: Automatic refresh, secure storage, lifecycle management

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Profile Agent                            │
│                                                             │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────┐  │
│  │   Agent Core    │  │  OAuth System   │  │ A2A Server  │  │
│  │  (agent.py)     │  │ (auth/*)        │  │(agent_a2a/*) │  │
│  └─────────────────┘  └─────────────────┘  └─────────────┘  │
│           │                     │                   │       │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────┐  │
│  │ Profile Tools   │  │ Token Storage   │  │  HTTP API   │  │
│  │ (tools/*)       │  │(credential_*)   │  │  Handlers   │  │
│  └─────────────────┘  └─────────────────┘  └─────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

## 📁 Project Structure

```
profile-agent/
├── src/
│   ├── agent.py                          # Main entry point - create_profile_agent()
│   ├── auth/                             # OAuth authentication system
│   │   ├── oauth_middleware.py           # OAuthMiddleware class
│   │   ├── credential_store.py           # Token storage (Memory/File/SecretManager)
│   │   └── auth_config.py               # Configuration management
│   ├── agent_a2a/                       # A2A protocol implementation
│   │   ├── server.py                    # AuthenticatedA2AServer class
│   │   ├── handlers.py                  # AuthenticatedRequestHandler class
│   │   └── agent_card.py               # AgentCardBuilder class
│   └── tools/                           # Profile tools
│       ├── authenticated_tool.py        # AuthenticatedTool base class
│       └── profile_tool.py             # ProfileTool & ProfileSummaryTool
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
3. Configure environment variables:

```bash
export GOOGLE_OAUTH_CLIENT_ID="your-client-id"
export GOOGLE_OAUTH_CLIENT_SECRET="your-client-secret"
```

### 3. Run the Agent

```bash
# Start the Profile Agent
cd src
python agent.py

# Agent starts on http://localhost:8001
# Agent card: http://localhost:8001/.well-known/agent-card.json
```

### 4. Test OAuth Flow

```bash
# Run the OAuth test client
python oauth_test_client.py

# Follow the device flow instructions:
# 1. Visit the provided Google URL
# 2. Enter the device code
# 3. Authorize the application
# 4. Get your profile information
```

## 🔧 Implementation Details

### Core Agent Implementation

#### **Main Entry Point** (`src/agent.py`)
```python
def create_profile_agent() -> Agent:
    """Creates the Profile Agent with OAuth authentication capabilities"""
    # Key functions:
    # - Loads OAuth configuration via load_auth_config()
    # - Creates ProfileTool and ProfileSummaryTool instances
    # - Wraps tools in FunctionTool for ADK integration
    # - Returns configured Agent with Gemini model
```

#### **Agent Tools** (`src/tools/profile_tool.py`)
```python
class ProfileTool(AuthenticatedTool):
    async def execute_authenticated(self, user_context, request_type="full_profile", specific_fields=None):
        """Retrieves user profile information with OAuth authentication"""

    async def execute_with_context(self, tool_context: ToolContext, request_type="full_profile", specific_fields=None):
        """ADK integration wrapper - gets OAuth context from session state"""

class ProfileSummaryTool(AuthenticatedTool):
    async def execute_authenticated(self, user_context, summary_style="friendly"):
        """Generates formatted profile summaries"""
```

### OAuth Authentication System

#### **OAuth Middleware** (`src/auth/oauth_middleware.py`)
```python
class OAuthMiddleware:
    async def initiate_auth(self, user_id: str, provider: str = None) -> dict:
        """Initiates OAuth Device Flow - returns verification URL and code"""

    async def complete_auth(self, session_id: str, authorization_code: str = None) -> dict:
        """Completes OAuth flow - exchanges code for tokens"""

    async def get_valid_token(self, user_id: str, provider: str = None) -> Optional[TokenData]:
        """Retrieves and validates stored OAuth tokens"""

    async def get_user_info(self, user_id: str, provider: str = None) -> dict:
        """Fetches user profile from OAuth provider API"""
```

#### **Token Storage** (`src/auth/credential_store.py`)
```python
class FileCredentialStore(CredentialStore):
    async def store_token(self, user_id: str, provider: str, token_data: TokenData):
        """Stores encrypted OAuth tokens to disk"""

    async def get_token(self, user_id: str, provider: str) -> Optional[TokenData]:
        """Retrieves and decrypts stored tokens"""

class SecretManagerCredentialStore(CredentialStore):
    """Google Cloud Secret Manager integration for production deployments"""
```

### A2A Server Implementation

#### **Authenticated Server** (`src/agent_a2a/server.py`)
```python
class AuthenticatedA2AServer:
    async def _handle_a2a_request(self, request: Request) -> Response:
        """Handles A2A protocol messages with authentication"""

    async def _handle_auth_initiate(self, request: Request) -> Response:
        """POST /auth/initiate - Starts OAuth flow"""

    async def _handle_auth_complete(self, request: Request) -> Response:
        """POST /auth/complete - Completes OAuth flow"""

    async def _handle_auth_status(self, request: Request) -> Response:
        """GET /auth/status - Check authentication status"""
```

#### **Request Handlers** (`src/agent_a2a/handlers.py`)
```python
class AuthenticatedRequestHandler(DefaultRequestHandler):
    async def handle_post(self, request: Request) -> Response:
        """Main A2A message processing with OAuth authentication"""

    async def _validate_authentication(self, auth_info: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """🔧 CRITICAL: Validates OAuth tokens and returns complete user context"""
        # Fixed to include "token": token in returned context

    async def _store_oauth_in_session_state(self, user_context: Dict[str, Any], body: bytes):
        """Stores OAuth context in ADK session for tool access"""

    async def _store_oauth_in_global_registry(self, user_context: Dict[str, Any]):
        """Fallback OAuth storage mechanism"""
```

### Authenticated Tool Base

#### **Tool Authentication** (`src/tools/authenticated_tool.py`)
```python
class AuthenticatedTool(ABC):
    @abstractmethod
    async def execute_authenticated(self, user_context: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """Abstract method for authenticated tool execution"""

    async def fetch_real_user_info(self, user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Fetches live user data from OAuth provider APIs"""

    async def _fetch_google_user_info(self, access_token: str) -> Dict[str, Any]:
        """Google UserInfo API integration"""
        # Calls: https://www.googleapis.com/oauth2/v2/userinfo
```

## 🔄 OAuth Flow Implementation

### Device Flow Process

1. **Authentication Initiation**
   - **Endpoint**: `POST /auth/initiate`
   - **Handler**: `AuthenticatedA2AServer._handle_auth_initiate()`
   - **Process**: Calls Google Device Authorization endpoint
   - **Response**: Returns verification URL and user code

2. **User Authorization**
   - **User Action**: Visits `https://www.google.com/device`
   - **Provider**: Google OAuth 2.0 authorization server
   - **Scopes**: `openid profile email userinfo.profile userinfo.email`

3. **Token Exchange**
   - **Endpoint**: `POST /auth/complete` (automatic polling)
   - **Handler**: `OAuthMiddleware.complete_auth()`
   - **Process**: Exchanges device code for access tokens
   - **Storage**: `CredentialStore.store_token()` with encryption

4. **Profile Access**
   - **A2A Message**: User sends "get my profile"
   - **Authentication**: `AuthenticatedRequestHandler.handle_post()`
   - **Tool Execution**: `ProfileTool.execute_with_context()`
   - **API Call**: Live Google UserInfo API request
   - **Response**: Personalized profile summary

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

### Request Security
- **HTTPS Enforcement**: Configurable HTTPS requirements
- **Token Validation**: Multi-level authentication validation
- **Scope Verification**: OAuth scope requirement enforcement
- **Session Isolation**: Secure ADK session state management

## 📊 API Endpoints

### A2A Protocol
| Endpoint | Method | Handler | Purpose |
|----------|--------|---------|---------|
| `/` | POST | `AuthenticatedRequestHandler.handle_post()` | A2A messages |
| `/.well-known/agent-card.json` | GET | `handle_get_card()` | Public agent card |
| `/agent/authenticatedExtendedCard` | GET | `handle_authenticated_extended_card()` | Auth card |

### OAuth Authentication
| Endpoint | Method | Handler | Purpose |
|----------|--------|---------|---------|
| `/auth/initiate` | POST | `_handle_auth_initiate()` | Start OAuth |
| `/auth/complete` | POST | `_handle_auth_complete()` | Complete OAuth |
| `/auth/status` | GET | `_handle_auth_status()` | Auth status |
| `/auth/revoke` | POST | `_handle_auth_revoke()` | Revoke tokens |

### Health & Monitoring
| Endpoint | Method | Handler | Purpose |
|----------|--------|---------|---------|
| `/health` | GET | `_handle_health()` | Service health |

## 🧪 Testing

### Test Client Usage (`oauth_test_client.py`)

```python
class ProfileAgentClient:
    async def initiate_oauth(self, user_id: str, provider: str = "google") -> dict:
        """Initiates OAuth flow and returns device code"""

    async def send_authenticated_message(self, message: str, user_id: str) -> dict:
        """Sends A2A message with OAuth authentication"""

# Usage:
client = ProfileAgentClient("http://localhost:8001")
auth_data = await client.initiate_oauth("user@example.com")
# User completes OAuth in browser
response = await client.send_authenticated_message("get my profile", "user@example.com")
```

### Example Test Flow
```bash
# 1. Start agent
python src/agent.py

# 2. Run test client
python oauth_test_client.py

# 3. Follow OAuth flow
# Visit: https://www.google.com/device
# Enter code: ABC-DEF-GHI

# 4. Get profile response
"Hi Fernando Lammoglia! I can see you're logged in with the email flammoglia@google.com..."
```

## ⚙️ Configuration

### Agent Configuration (`config/agent_config.yaml`)
```yaml
agent:
  name: "${AGENT_NAME:ProfileAgent}"
  model:
    name: "${MODEL_NAME:gemini-2.0-flash}"

skills:
  - id: "user_profile_access"
    name: "User Profile Access"
    description: "Retrieves user profile information using OAuth authentication"

  - id: "profile_summary"
    name: "Profile Summary"
    description: "Provides a formatted summary of user profile data"
```

### OAuth Configuration (`config/oauth_config.yaml`)
```yaml
oauth:
  default_provider: "${OAUTH_DEFAULT_PROVIDER:google}"
  flow_type: "${OAUTH_FLOW_TYPE:device_flow}"

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
```bash
# Required OAuth Configuration
GOOGLE_OAUTH_CLIENT_ID=your-client-id
GOOGLE_OAUTH_CLIENT_SECRET=your-client-secret

# Agent Configuration
AGENT_NAME=ProfileAgent
MODEL_NAME=gemini-2.0-flash
A2A_PORT=8001

# Security & Storage
TOKEN_STORAGE_TYPE=file  # file, memory, secret_manager
OAUTH_REQUIRE_HTTPS=true
LOG_LEVEL=INFO
```

## 🚀 Deployment

### Local Development
```bash
# Set environment variables
export GOOGLE_OAUTH_CLIENT_ID="your-client-id"
export GOOGLE_OAUTH_CLIENT_SECRET="your-client-secret"

# Run agent
python src/agent.py

# Test with client
python oauth_test_client.py
```

### Cloud Run Deployment
```bash
# Build and deploy
gcloud run deploy profile-agent \
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
- **Cause**: Missing OAuth token in user context (Fixed in latest version)
- **Solution**: Ensure `_validate_authentication()` includes `"token": token` in response
- **File**: `src/agent_a2a/handlers.py:242`

#### OAuth Flow Failure
- **Check**: OAuth client ID/secret configuration
- **Verify**: Network access to Google OAuth endpoints
- **Debug**: Enable debug logging with `LOG_LEVEL=DEBUG`

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

## 📋 Production Checklist

- ✅ **OAuth Configuration**: Valid client ID/secret configured
- ✅ **HTTPS Enforcement**: TLS certificates and HTTPS redirect
- ✅ **Token Storage**: Secure storage (Secret Manager for production)
- ✅ **Environment Variables**: All required variables set
- ✅ **Network Security**: Firewall rules and VPC configuration
- ✅ **Monitoring**: Logging and error tracking configured
- ✅ **Testing**: End-to-end OAuth flow validation
- ✅ **Documentation**: API documentation and runbooks

## 📖 Additional Resources

- **Detailed Implementation Report**: See `PROFILE_AGENT_REPORT.md` for comprehensive technical details
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

**Profile Agent** - Production-ready OAuth-authenticated AI agent built with Google ADK 🚀