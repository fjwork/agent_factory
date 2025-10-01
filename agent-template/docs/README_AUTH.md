# Authentication System Documentation

This directory (src/auth) contains the complete authentication system for the ADK agent template, providing OAuth 2.0 authentication with multiple providers, bearer token support, and secure credential management.

## Overview

The authentication system supports two primary authentication patterns:
1. **OAuth Device Flow** - Interactive user authentication via OAuth providers
2. **Bearer Token Authentication** - Pre-authenticated requests from web apps or orchestrator agents

Both patterns provide unified user context to agent tools and support authentication forwarding to remote agents via A2A protocol.

## Authentication Flow

### How Authentication Works

The system uses **Dual Authentication Middleware** as the primary entry point that intelligently detects and handles different authentication methods. Here's the normal user flow:

#### 1. Request Processing (Priority Order)
```
Incoming Request → DualAuthMiddleware.extract_auth_context()
```

**Priority 1: Bearer Token Detection**
```bash
# Check Authorization header
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
```
- If bearer token found → Validate JWT → Create user context ✅
- If validation fails → Continue to Priority 2

**Priority 2: OAuth Session Check**
```bash
# Check request body for user_id
{"user_id": "user@example.com", "message": "..."}
```
- If user_id found → Check stored tokens → Create user context ✅
- If no valid tokens found → Continue to Priority 3

**Priority 3: OAuth Device Flow Initiation**
```bash
# No authentication found
Response: {"error": "authentication_required", "oauth_initiation_url": "/auth/initiate"}
```

#### 2. User Experience Scenarios

**Scenario A: Web App User (Bearer Token)**
```
1. User logs into web app
2. Web app obtains JWT token
3. Web app makes request: Authorization: Bearer <token>
4. Agent validates JWT → Immediate access ✅
```

**Scenario B: CLI User (OAuth Device Flow)**
```
1. User makes request without auth
2. Agent responds: "Visit https://accounts.google.com/... and enter code: ABC123"
3. User completes OAuth in browser
4. Agent polls for completion
5. Agent stores tokens → Future requests use stored session ✅
```

**Scenario C: Returning CLI User (Stored Session)**
```
1. User makes request with user_id in body
2. Agent finds valid stored tokens
3. Agent uses stored tokens → Immediate access ✅
```

#### 3. Authentication Context Flow
```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   HTTP Request  │    │  Dual Auth       │    │  Agent Tools    │
│                 │───►│  Middleware      │───►│                 │
│ • Bearer token  │    │                  │    │ • User context  │
│ • user_id       │    │ Priority check   │    │ • Access token  │
│ • No auth       │    │ Context creation │    │ • User info     │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌──────────────────┐
                       │  OAuth           │
                       │  Middleware      │
                       │                  │
                       │ • Device flow    │
                       │ • Token refresh  │
                       │ • User info      │
                       └──────────────────┘
                                │
                                ▼
                       ┌──────────────────┐
                       │  Credential      │
                       │  Store           │
                       │                  │
                       │ • Token storage  │
                       │ • Encryption     │
                       │ • Expiration     │
                       └──────────────────┘
```

#### 4. Multi-Agent Authentication Forwarding
```
Root Agent (authenticated) → A2A Protocol → Remote Agent
```
- **Bearer tokens** automatically forwarded in A2A headers
- **OAuth context** (user info, tokens) forwarded in session state
- **Remote agents** receive same authentication context as root agent

## Architecture

```
┌─────────────────────┐    ┌──────────────────────┐    ┌─────────────────────┐
│  Dual Auth          │    │  OAuth Middleware    │    │  Credential Store   │
│  Middleware         │◄──►│                      │◄──►│                     │
│                     │    │                      │    │                     │
│ • Bearer tokens     │    │ • Device flow        │    │ • Memory storage    │
│ • OAuth sessions    │    │ • Auth code flow     │    │ • File storage      │
│ • Context unified   │    │ • Client credentials │    │ • Secret Manager    │
└─────────────────────┘    └──────────────────────┘    └─────────────────────┘
            │                           │                           │
            └─────────────────┬─────────────────────────────────────┘
                              │
                    ┌─────────▼─────────┐
                    │   Auth Config     │
                    │                   │
                    │ • YAML config     │
                    │ • Multi-provider  │
                    │ • Environment     │
                    │   overrides       │
                    └───────────────────┘
```

## File Descriptions

### `oauth_middleware.py`
**Purpose**: Core OAuth 2.0 authentication flows and token management

**Main Classes:**
- `OAuthMiddleware` - Primary OAuth handler

**Key Functions:**
- `initiate_auth(user_id, provider)` - Start OAuth flow
- `complete_auth(session_id, **kwargs)` - Complete OAuth flow
- `get_valid_token(user_id, provider)` - Get/refresh valid tokens
- `get_user_info(user_id, provider)` - Fetch user profile
- `revoke_token(user_id, provider)` - Revoke authentication
- `validate_jwt_token(token, provider)` - JWT validation

**Supported OAuth Flows:**
1. **Device Flow** (`_initiate_device_flow`)
   - Best for: CLI tools, IoT devices, headless environments
   - User visits URL and enters device code
   - Polling-based completion

2. **Authorization Code Flow** (`_initiate_authorization_code_flow`)
   - Best for: Web applications with redirect capability
   - CSRF protection with state parameter
   - Requires redirect URI handling

3. **Client Credentials Flow** (`_initiate_client_credentials_flow`)
   - Best for: Machine-to-machine authentication
   - Service account authentication
   - No user interaction required

**Token Management:**
- Automatic token refresh using refresh tokens
- Session state management for pending flows
- Expiration checking and cleanup
- Provider-specific token handling

### `dual_auth_middleware.py`
**Purpose**: Unified authentication layer supporting both bearer tokens and OAuth flows

**Main Class:**
- `DualAuthMiddleware` - Primary authentication coordinator

**Key Functions:**
- `extract_auth_context(request)` - Detect and process authentication
- `_validate_bearer_token(token)` - Bearer token validation
- `_normalize_user_context(auth_data, auth_type)` - Unified context format
- `initiate_device_flow(user_id, provider)` - OAuth fallback

**Authentication Priority Order:**
1. **Bearer Token** (Authorization header)
2. **OAuth Session** (stored tokens)
3. **Device Flow Initiation** (new users)

**Bearer Token Validation Modes:**
- `BEARER_TOKEN_VALIDATION=valid` - Mock success (testing)
- `BEARER_TOKEN_VALIDATION=invalid` - Mock failure (testing)
- `BEARER_TOKEN_VALIDATION=jwt` - JWT validation (production)

**Context Normalization:**
Ensures both OAuth and bearer token flows produce compatible user contexts:
```json
{
  "user_id": "user@example.com",
  "provider": "google|bearer_token",
  "user_info": {"name": "...", "email": "..."},
  "token": "access_token",
  "auth_type": "oauth|bearer",
  "authenticated": true
}
```

### `credential_store.py`
**Purpose**: Secure storage and retrieval of OAuth tokens with multiple backend options

**Abstract Base:**
- `CredentialStore` - Interface for all storage implementations

**Storage Implementations:**

#### `MemoryCredentialStore`
- **Use Case**: Development, testing, single-instance deployments
- **Features**: Optional in-memory encryption, automatic cleanup
- **Limitations**: Tokens lost on restart
- **Security**: Generated encryption keys (not persistent)

#### `FileCredentialStore`
- **Use Case**: Single-instance production, local development
- **Features**: AES-256 encryption, persistent key management
- **Security**: User ID hashing, file permissions (0600), encrypted storage
- **Storage Location**: `.credentials/` directory (configurable)

#### `GoogleCloudCredentialStore`
- **Use Case**: Production, distributed deployments, enterprise
- **Features**: Secret Manager integration, automatic versioning
- **Security**: Master key management, cloud-native encryption
- **Requirements**: Google Cloud project, Secret Manager API

**Common Interface:**
- `store_token(user_id, provider, token_data)` - Store encrypted tokens
- `get_token(user_id, provider)` - Retrieve valid tokens
- `delete_token(user_id, provider)` - Remove tokens
- `list_user_tokens(user_id)` - List all user's active tokens

**Security Features:**
- Automatic expiration handling
- Token encryption at rest
- Privacy-preserving user ID hashing
- Secure key management per backend

### `auth_config.py`
**Purpose**: Configuration management with environment-specific overrides

**Main Classes:**
- `AuthConfig` - Master configuration container
- `ConfigLoader` - Environment-aware configuration loading
- `OAuthProvider` - Provider-specific settings
- `SecurityScheme` - A2A security definitions

**Key Functions:**
- `load_auth_config(environment)` - Load configuration for environment
- `get_oauth_provider(provider_name)` - Get provider configuration
- `get_security_schemes()` - Get A2A security schemes

**Configuration Structure:**
```yaml
oauth:
  default_provider: "google"
  flow_type: "device_flow"
  scopes: ["openid", "email", "profile"]

providers:
  google:
    client_id: "${GOOGLE_OAUTH_CLIENT_ID}"
    client_secret: "${GOOGLE_OAUTH_CLIENT_SECRET}"
    authorization_url: "https://accounts.google.com/o/oauth2/auth"
    # ... more endpoints

environments:
  development:
    oauth:
      flow_type: "device_flow"
  production:
    oauth:
      require_https: true
```

**Environment Variable Expansion:**
- `${VAR:default}` syntax for flexible configuration
- Environment-specific overrides
- Secure credential management

### `agent_auth_callback.py`
**Purpose**: Authentication context injection for ADK agent lifecycle

**Key Function:**
- `auth_context_callback(agent, request)` - Inject auth context into agent session

**Integration Points:**
- Called before agent processing via `before_agent_callback`
- Updates agent's remote sub-agents with authentication context
- Enables authentication forwarding to remote agents

**Workflow:**
1. Extract authentication from request
2. Reload agent with authentication context
3. Update sub-agents for A2A authentication forwarding
4. Continue with agent processing

## Configuration Files

### Required: `config/oauth_config.yaml`
OAuth provider configuration with environment overrides.

**Example Structure:**
```yaml
oauth:
  default_provider: "google"
  flow_type: "device_flow"
  scopes: ["openid", "email", "profile"]

  token_storage:
    type: "file"  # memory|file|secret_manager
    encryption: true
    ttl_seconds: 3600

  security:
    validate_issuer: true
    validate_audience: true
    require_https: true

providers:
  google:
    client_id: "${GOOGLE_OAUTH_CLIENT_ID}"
    client_secret: "${GOOGLE_OAUTH_CLIENT_SECRET}"
    authorization_url: "https://accounts.google.com/o/oauth2/auth"
    token_url: "https://oauth2.googleapis.com/token"
    device_authorization_url: "https://oauth2.googleapis.com/device/code"
    userinfo_url: "https://openidconnect.googleapis.com/v1/userinfo"
    default_scopes: ["openid", "email", "profile"]

environments:
  development:
    oauth:
      token_storage:
        type: "memory"
    logging:
      level: "DEBUG"

  production:
    oauth:
      token_storage:
        type: "secret_manager"
      security:
        require_https: true
      logging:
        level: "WARNING"
```

## Environment Variables

### Required OAuth Credentials
```bash
# Google OAuth (required)
GOOGLE_OAUTH_CLIENT_ID="your-client-id"
GOOGLE_OAUTH_CLIENT_SECRET="your-client-secret"

# Azure OAuth (optional)
AZURE_OAUTH_CLIENT_ID="your-azure-client-id"
AZURE_OAUTH_CLIENT_SECRET="your-azure-client-secret"

# Google Cloud (for Secret Manager storage)
GOOGLE_CLOUD_PROJECT="your-project-id"
```

### Authentication Testing
```bash
# Bearer token validation mode
BEARER_TOKEN_VALIDATION="jwt"  # jwt|valid|invalid

# Environment
ENVIRONMENT="development"  # development|staging|production

# Logging
LOG_LEVEL="INFO"  # DEBUG|INFO|WARNING|ERROR
```

## Integration with Agent Tools

### Tool Authentication Context
Agent tools receive authentication context via `execute_with_context`:

```python
async def execute_with_context(self, **kwargs):
    # Extract session state with auth context
    session_state = kwargs.get('session_state', {})

    # Get authentication context
    auth_context = session_state.get('auth_context')

    if auth_context and auth_context.get('authenticated'):
        # Use authenticated context
        user_info = auth_context.get('user_info', {})
        access_token = auth_context.get('token')

        # Make authenticated API calls
        return await self.execute_authenticated(auth_context, **kwargs)
    else:
        # Handle unauthenticated requests
        return {"error": "Authentication required"}
```

### A2A Authentication Forwarding
Authentication context is automatically forwarded to remote agents:

```python
# In remote agent factory
remote_agents_with_auth = await factory.load_remote_agents_if_configured(auth_context)

# Authentication context includes:
# - Bearer tokens
# - OAuth context
# - User information
# - Provider details
```

## Testing

### Unit Testing
```bash
# Test OAuth flows
python -m pytest tests/auth/test_oauth_middleware.py

# Test bearer token validation
python -m pytest tests/auth/test_dual_auth.py

# Test credential storage
python -m pytest tests/auth/test_credential_store.py
```

### Integration Testing
```bash
# Test complete authentication flows
python testing_scripts/oauth_test_client.py

# Test bearer token forwarding
python testing_scripts/bearer_token_test_client.py

# Test multi-agent authentication forwarding
python testing_scripts/test_multiagent.sh
```

### Manual Testing
```bash
# Test OAuth device flow
curl -X POST http://localhost:8001/auth/initiate \
  -H "Content-Type: application/json" \
  -d '{"user_id": "test@example.com", "provider": "google"}'

# Test bearer token
curl -X POST http://localhost:8001/ \
  -H "Authorization: Bearer your-token" \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc": "2.0", "method": "message/send", ...}'
```

## Production Readiness

### ✅ Production Ready
- OAuth 2.0 device flow implementation
- Bearer token authentication
- Secure credential storage options
- Multi-provider support
- Environment-specific configuration
- Token refresh and lifecycle management
- Authentication context forwarding
- Comprehensive error handling

### ⚠️ Needs Attention Before Production

#### Security Enhancements
1. **JWT Signature Verification**
   - Current: Basic JWT decoding without signature verification
   - **Required**: Implement proper JWKS-based signature validation
   - **Impact**: Critical for bearer token security

2. **Token Introspection**
   - Current: Basic expiration checking
   - **Required**: OAuth token introspection endpoint support
   - **Impact**: Better token validation and revocation

3. **Rate Limiting**
   - Current: No rate limiting on auth endpoints
   - **Required**: Implement rate limiting for auth flows
   - **Impact**: Prevent abuse and DoS attacks

#### Monitoring & Observability
1. **Audit Logging**
   - Current: Basic debug logging
   - **Required**: Structured audit logs for authentication events
   - **Impact**: Compliance and security monitoring

2. **Metrics Collection**
   - Current: No metrics
   - **Required**: Authentication success/failure metrics
   - **Impact**: Operational visibility

3. **Health Checks**
   - Current: Basic health endpoint
   - **Required**: Authentication-specific health checks
   - **Impact**: Better monitoring of auth dependencies

#### Compliance & Standards
1. **PKCE Support**
   - Current: Basic authorization code flow
   - **Required**: PKCE (Proof Key for Code Exchange) for mobile/SPA
   - **Impact**: Enhanced security for public clients

2. **OpenID Connect Compliance**
   - Current: Basic OAuth 2.0
   - **Required**: Full OIDC compliance with proper claims handling
   - **Impact**: Better interoperability

#### Operational Requirements
1. **Key Rotation**
   - Current: Static encryption keys
   - **Required**: Automated key rotation for encryption keys
   - **Impact**: Long-term security

2. **Backup & Recovery**
   - Current: No backup strategy for stored tokens
   - **Required**: Token backup and recovery procedures
   - **Impact**: Business continuity

3. **Multi-tenancy**
   - Current: Single-tenant design
   - **Required**: Multi-tenant token isolation if needed
   - **Impact**: Enterprise deployments

### 📋 Implementation Priority

#### High Priority (Security Critical)
1. **JWT Signature Verification** - Implement proper JWKS validation
2. **Rate Limiting** - Add rate limiting to auth endpoints
3. **Audit Logging** - Structured authentication event logging

#### Medium Priority (Operational)
1. **Token Introspection** - OAuth introspection endpoint support
2. **Metrics Collection** - Authentication metrics and monitoring
3. **Key Rotation** - Automated encryption key rotation

#### Low Priority (Enhancement)
1. **PKCE Support** - Enhanced authorization code flow security
2. **Multi-tenancy** - If multi-tenant deployment needed
3. **Backup Strategy** - Token backup and recovery procedures

## Error Handling

### Common Error Scenarios
1. **Invalid OAuth Configuration** - Missing client credentials
2. **Expired Tokens** - Automatic cleanup and refresh
3. **Network Failures** - Retry logic for OAuth endpoints
4. **Storage Failures** - Graceful degradation for credential store issues
5. **Invalid Bearer Tokens** - Proper 401 responses

### Error Response Format
```json
{
  "error": "authentication_required",
  "message": "Valid authentication required",
  "details": {
    "supported_methods": ["bearer", "oauth_device_flow"],
    "oauth_initiation_url": "/auth/initiate"
  }
}
```

## Best Practices

### Development
- Use `BEARER_TOKEN_VALIDATION=valid` for local testing
- Use memory storage for development environments
- Enable debug logging for troubleshooting

### Production
- Use Secret Manager for credential storage
- Enable HTTPS enforcement
- Implement proper JWT validation
- Monitor authentication metrics
- Regular security audits

### Multi-Agent Deployments
- Ensure authentication context forwarding is tested
- Verify bearer token propagation across agent boundaries
- Test remote agent authentication isolation

---

## Support

For implementation questions or issues:
1. Check the troubleshooting guide: `docs/troubleshooting.md`
2. Review test examples in `testing_scripts/`
3. Examine configuration templates in `docs/configurations/`

This authentication system provides enterprise-grade security foundations while maintaining flexibility for different deployment scenarios and authentication patterns.