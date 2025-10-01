# Agent-to-Agent (A2A) Protocol Implementation

This directory (src/agent_a2a) contains the complete Agent-to-Agent (A2A) protocol implementation with OAuth authentication integration. The A2A system enables secure communication between agents, multi-agent orchestration, and authentication context forwarding.

## Overview

The A2A implementation provides:
1. **A2A Protocol Server** - HTTP/JSON-RPC server for agent communication
2. **Authentication Integration** - OAuth and bearer token support for secure A2A calls
3. **Agent Card Generation** - Dynamic agent capability discovery and advertising
4. **Request Handling** - Authenticated request processing and context forwarding
5. **Multi-Agent Support** - Foundation for orchestrating multiple specialized agents

## A2A Protocol Flow

### How A2A Communication Works

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Root Agent    │    │  A2A Protocol    │    │  Remote Agent   │
│                 │───►│   (HTTP/JSON)    │───►│                 │
│ • User request  │    │                  │    │ • Specialized   │
│ • Auth context  │    │ • Auth forward   │    │   capability    │
│ • Task delegation│   │ • Session state  │    │ • Auth context  │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

#### 1. Agent Card Discovery
```bash
# Each agent exposes its capabilities
GET /.well-known/agent-card.json

{
  "name": "DataAnalysisAgent",
  "version": "1.0.0",
  "description": "Specialized data analysis agent",
  "capabilities": ["data_analysis", "visualization"],
  "security": ["oauth2", "bearerAuth"]
}
```

#### 2. Authenticated A2A Request
```bash
# Root agent delegates task to remote agent
POST / HTTP/1.1
Authorization: Bearer <forwarded-token>
Content-Type: application/json

{
  "jsonrpc": "2.0",
  "id": "task-123",
  "method": "message/send",
  "params": {
    "message": {
      "messageId": "msg-456",
      "role": "user",
      "parts": [{"text": "Analyze sales data with trend analysis"}]
    }
  }
}
```

#### 3. Authentication Context Forwarding
```python
# Authentication automatically forwarded in session state
session_state = {
    "auth_context": {
        "user_id": "user@example.com",
        "provider": "google",
        "token": "access_token",
        "user_info": {"name": "...", "email": "..."},
        "authenticated": True
    }
}
```

## File Descriptions

### `server.py`
**Purpose**: Main A2A server implementation with OAuth authentication integration

**Main Class:**
- `AuthenticatedA2AServer` - Primary A2A server with authentication

**Key Components:**
```python
# Core server setup
def __init__(self, agent, config_dir, environment):
    self.oauth_middleware = OAuthMiddleware()      # OAuth handling
    self.card_builder = AgentCardBuilder()        # Agent card generation
    self.runner = self._create_runner()           # ADK runner
    self.executor = self._create_executor()       # A2A executor
    self.request_handler = AuthenticatedRequestHandler()  # Auth request handling
```

**A2A Protocol Routes:**
- `POST /` - Main A2A message endpoint (authenticated)
- `GET /.well-known/agent-card.json` - Agent capability discovery
- `GET /agent/authenticatedExtendedCard` - Extended agent card with auth info

**OAuth Authentication Routes:**
- `POST /auth/initiate` - Start OAuth device flow
- `POST /auth/complete` - Complete OAuth flow
- `GET /auth/status` - Check authentication status
- `POST /auth/revoke` - Revoke tokens
- `GET /auth/dual-status` - Check dual auth status (Bearer + OAuth)

**Health & Monitoring:**
- `GET /health` - Health check with authentication status

**Key Functions:**
- `_handle_a2a_request()` - Process authenticated A2A requests
- `_handle_auth_initiate()` - OAuth flow initiation
- `_handle_dual_auth_status()` - Dual authentication status
- `build()` - Return configured Starlette application

**ADK Integration:**
```python
def _create_runner(self) -> Runner:
    return Runner(
        app_name=self.agent.name,
        agent=self.agent,
        artifact_service=InMemoryArtifactService(),
        session_service=InMemorySessionService(),
        memory_service=InMemoryMemoryService()
    )

def _create_executor(self) -> A2aAgentExecutor:
    return A2aAgentExecutor(
        runner=self.runner,
        config=A2aAgentExecutorConfig()
    )
```

### `handlers.py`
**Purpose**: Authenticated request handling with dual authentication support

**Main Class:**
- `AuthenticatedRequestHandler` - Extends ADK's DefaultRequestHandler with authentication

**Authentication Flow:**
```python
async def handle_post(self, request: Request) -> Response:
    # 1. Extract authentication context (Bearer token or OAuth)
    user_context = await self.dual_auth_middleware.extract_auth_context(request)

    # 2. Validate authentication
    if not user_context or not user_context.get("authenticated"):
        return JSONResponse({"error": "Authentication required"}, status_code=401)

    # 3. Store context in session state
    await self._store_oauth_in_session_state(user_context, body)

    # 4. Inject auth into agent's remote agents
    await self._inject_auth_context_into_agent(user_context)

    # 5. Process A2A request
    return await super().handle_post(request)
```

**Key Functions:**
- `handle_post()` - Main A2A request processing with authentication
- `handle_authenticated_extended_card()` - Extended agent card for authenticated users
- `handle_auth_status()` - Authentication status endpoint
- `_store_oauth_in_session_state()` - Store auth context in ADK session
- `_inject_auth_context_into_agent()` - Forward auth to remote agents
- `_extract_auth_info()` - Extract authentication from session state

**Session State Management:**
```python
async def _store_oauth_in_session_state(self, user_context, body):
    # Store authentication context in ADK session state
    session_state = {
        "auth_context": user_context,
        "oauth_authenticated": True,
        "oauth_user_id": user_context.get("user_id"),
        "oauth_provider": user_context.get("provider"),
        "oauth_token": user_context.get("token"),
        "oauth_user_info": user_context.get("user_info", {})
    }
```

**Authentication Context Injection:**
```python
async def _inject_auth_context_into_agent(self, user_context):
    # Update agent's remote agents with authentication context
    if hasattr(self.agent_executor.runner.agent, '_remote_factory'):
        await reload_agent_with_auth_context(
            self.agent_executor.runner.agent,
            user_context
        )
```

### `agent_card.py`
**Purpose**: Dynamic A2A agent card generation with security schemes

**Main Class:**
- `AgentCardBuilder` - Creates A2A-compliant agent cards

**Configuration Loading:**
```python
def load_agent_config(self, environment: str) -> Dict[str, Any]:
    # Load from config/agent_config.yaml
    # Apply environment overrides
    # Expand environment variables
    return config_data
```

**Agent Card Creation:**
```python
def create_agent_card(self, environment: str) -> AgentCard:
    config = self.load_agent_config(environment)

    # Create card components
    capabilities = AgentCapabilities(streaming=True)
    skills = [AgentSkill(...) for skill in skills_config]
    security_schemes = self._create_security_schemes()

    return AgentCard(
        name=agent_name,
        version=version,
        description=description,
        capabilities=capabilities,
        skills=skills,
        security_schemes=security_schemes,
        # ... other fields
    )
```

**Security Schemes Integration:**
```python
def _create_security_schemes(self) -> Dict[str, Any]:
    # Load from OAuth config
    schemes = get_security_schemes()

    return {
        "oauth2": {
            "type": "oauth2",
            "flows": {
                "authorizationCode": {
                    "authorizationUrl": "https://accounts.google.com/o/oauth2/auth",
                    "tokenUrl": "https://oauth2.googleapis.com/token"
                }
            }
        },
        "bearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT"
        }
    }
```

**Agent Card Structure:**
```json
{
  "name": "AuthenticatedAgent",
  "version": "1.0.0",
  "description": "Agent with OAuth authentication",
  "url": "http://localhost:8000",
  "capabilities": {
    "streaming": true,
    "push_notifications": false,
    "authenticated_extended_card": true
  },
  "skills": [
    {
      "id": "authenticated_operations",
      "name": "Authenticated Operations",
      "description": "OAuth-enabled operations",
      "examples": ["Access my data", "Show my profile"]
    }
  ],
  "security_schemes": {
    "oauth2": { "type": "oauth2", "flows": {...} },
    "bearerAuth": { "type": "http", "scheme": "bearer" }
  },
  "security": [
    {"oauth2": ["agent_access"]},
    {"bearerAuth": []}
  ]
}
```

## A2A Protocol Endpoints

### Core A2A Endpoints

| Endpoint | Method | Purpose | Authentication |
|----------|--------|---------|----------------|
| `/` | POST | A2A message processing | Required |
| `/.well-known/agent-card.json` | GET | Agent capability discovery | None |
| `/agent/authenticatedExtendedCard` | GET | Extended agent card | Required |

### Authentication Endpoints

| Endpoint | Method | Purpose | Description |
|----------|--------|---------|-------------|
| `/auth/initiate` | POST | Start OAuth flow | Initiate device/auth code flow |
| `/auth/complete` | POST | Complete OAuth flow | Exchange code for tokens |
| `/auth/status` | GET | Check auth status | Get user authentication state |
| `/auth/revoke` | POST | Revoke tokens | Logout/revoke access |
| `/auth/dual-status` | GET/POST | Dual auth status | Bearer + OAuth support info |

### Health & Monitoring

| Endpoint | Method | Purpose | Response |
|----------|--------|---------|----------|
| `/health` | GET | Health check | Service + auth status |

## Authentication Integration

### Bearer Token Flow
```bash
# 1. Request with bearer token
POST / HTTP/1.1
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...

# 2. Server validates JWT and extracts user context
# 3. Request processed with authenticated context
```

### OAuth Device Flow
```bash
# 1. Initiate OAuth flow
POST /auth/initiate
{"user_id": "user@example.com", "provider": "google"}

# 2. Response with device code
{
  "verification_url": "https://accounts.google.com/device",
  "user_code": "ABC-123",
  "device_code": "...",
  "expires_in": 1800
}

# 3. User authorizes in browser
# 4. Complete flow (polling or callback)
POST /auth/complete
{"session_id": "session-id"}

# 5. Future requests use stored session
POST /
{"user_id": "user@example.com", "message": "..."}
```

### Multi-Agent Authentication Forwarding
```python
# Root agent automatically forwards authentication to remote agents
def delegate_to_remote_agent(self, task, user_context):
    # Authentication context automatically included in A2A request
    response = await remote_agent.call({
        "jsonrpc": "2.0",
        "method": "message/send",
        "params": {"message": task},
        # user_context automatically forwarded in session state
    })
```

## Configuration

### Required Configuration Files

#### `config/agent_config.yaml`
```yaml
agent:
  name: "MyAgent"
  version: "1.0.0"
  description: "Agent description"

capabilities:
  streaming: true
  authenticated_extended_card: true

skills:
  - id: "skill_1"
    name: "Skill Name"
    description: "Skill description"
    examples: ["Example 1", "Example 2"]

a2a:
  host: "0.0.0.0"
  port: 8000
  agent_card:
    url: "http://localhost:8000"
```

#### `config/oauth_config.yaml`
```yaml
oauth:
  default_provider: "google"
  flow_type: "device_flow"

providers:
  google:
    client_id: "${GOOGLE_OAUTH_CLIENT_ID}"
    client_secret: "${GOOGLE_OAUTH_CLIENT_SECRET}"

a2a_auth:
  security_schemes:
    oauth2:
      type: "oauth2"
      flows: {...}
    bearerAuth:
      type: "http"
      scheme: "bearer"
```

## Usage Examples

### Starting A2A Server
```python
from agent_a2a.server import create_authenticated_a2a_server

# Create agent (from ADK)
agent = Agent(model="gemini-2.0-flash", name="MyAgent", ...)

# Create A2A server with authentication
server = create_authenticated_a2a_server(
    agent=agent,
    config_dir="config",
    environment="development"
)

# Start server
app = server.build()
uvicorn.run(app, host="0.0.0.0", port=8000)
```

### Making Authenticated A2A Calls
```python
import httpx

# With bearer token
headers = {"Authorization": "Bearer <token>"}
response = await httpx.post(
    "http://localhost:8000/",
    headers=headers,
    json={
        "jsonrpc": "2.0",
        "id": "1",
        "method": "message/send",
        "params": {
            "message": {
                "messageId": "msg-1",
                "role": "user",
                "parts": [{"text": "Hello from authenticated user"}]
            }
        }
    }
)

# With OAuth session
response = await httpx.post(
    "http://localhost:8000/",
    json={
        "jsonrpc": "2.0",
        "id": "1",
        "method": "message/send",
        "params": {
            "message": {
                "messageId": "msg-1",
                "role": "user",
                "parts": [{"text": "Hello from OAuth user"}]
            }
        },
        "user_id": "user@example.com"  # OAuth session lookup
    }
)
```

### Remote Agent Integration
```python
# config/remote_agents.yaml
remote_agents:
  - name: "data_analysis_agent"
    description: "Data analysis specialist"
    agent_card_url: "http://localhost:8002"
    enabled: true

# Authentication automatically forwarded to remote agents
# Remote agents receive same user context as root agent
```

## Testing

### Unit Testing
```bash
# Test A2A server creation
python -m pytest tests/agent_a2a/test_server.py

# Test authentication handling
python -m pytest tests/agent_a2a/test_handlers.py

# Test agent card generation
python -m pytest tests/agent_a2a/test_agent_card.py
```

### Integration Testing
```bash
# Test complete A2A flow with authentication
python testing_scripts/test_a2a_auth.py

# Test multi-agent authentication forwarding
python testing_scripts/test_multiagent.sh

# Test bearer token A2A calls
python testing_scripts/bearer_token_test_client.py
```

### Manual Testing
```bash
# Start agent
python src/agent.py

# Test agent card
curl http://localhost:8000/.well-known/agent-card.json

# Test health
curl http://localhost:8000/health

# Test OAuth initiation
curl -X POST http://localhost:8000/auth/initiate \
  -H "Content-Type: application/json" \
  -d '{"user_id": "test@example.com"}'

# Test A2A with bearer token
curl -X POST http://localhost:8000/ \
  -H "Authorization: Bearer test-token" \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc": "2.0", "method": "message/send", ...}'
```

## Production Considerations

### ✅ Production Ready
- A2A protocol compliance
- OAuth and bearer token authentication
- Session state management
- Agent card generation
- Multi-agent authentication forwarding
- Health monitoring
- Error handling and logging

### ⚠️ Needs Attention Before Production

#### Security Enhancements
1. **HTTPS Enforcement**
   - Current: HTTP support for development
   - **Required**: Force HTTPS in production
   - **Impact**: Secure A2A communication

2. **Request Validation**
   - Current: Basic JSON-RPC validation
   - **Required**: Schema validation for all A2A requests
   - **Impact**: Prevent malformed requests

3. **Rate Limiting**
   - Current: No rate limiting on A2A endpoints
   - **Required**: Rate limiting per user/agent
   - **Impact**: Prevent abuse and DoS

#### Scalability & Performance
1. **Session Management**
   - Current: In-memory session storage
   - **Required**: Distributed session storage (Redis/database)
   - **Impact**: Multi-instance deployment support

2. **Connection Pooling**
   - Current: New connections for each A2A call
   - **Required**: HTTP connection pooling for remote agents
   - **Impact**: Performance optimization

3. **Async Processing**
   - Current: Synchronous A2A processing
   - **Required**: Async/queue-based processing for long tasks
   - **Impact**: Better responsiveness

#### Monitoring & Observability
1. **A2A Metrics**
   - Current: Basic logging
   - **Required**: A2A call metrics (latency, success rate, etc.)
   - **Impact**: Operational visibility

2. **Distributed Tracing**
   - Current: No tracing across A2A calls
   - **Required**: Trace IDs across multi-agent calls
   - **Impact**: Debugging complex workflows

3. **Agent Health Monitoring**
   - Current: Simple health check
   - **Required**: Agent dependency health checks
   - **Impact**: Better failure detection

## Error Handling

### A2A Protocol Errors
```json
{
  "jsonrpc": "2.0",
  "id": "request-id",
  "error": {
    "code": -32600,
    "message": "Invalid Request",
    "data": {"details": "Missing required field"}
  }
}
```

### Authentication Errors
```json
{
  "error": "Authentication required",
  "message": "This endpoint requires authentication",
  "supported_methods": ["bearer", "oauth_device_flow"],
  "details": {
    "bearer_token": {
      "header": "Authorization: Bearer <token>"
    },
    "oauth_device_flow": {
      "initiation_url": "/auth/initiate"
    }
  }
}
```

### Remote Agent Errors
```json
{
  "error": "remote_agent_unavailable",
  "message": "Remote agent not accessible",
  "agent": "data_analysis_agent",
  "endpoint": "http://localhost:8002"
}
```

## Best Practices

### Development
- Use HTTP for local development
- Enable CORS for web clients
- Use debug logging for A2A calls
- Test with mock remote agents

### Production
- Force HTTPS for all A2A communication
- Use distributed session storage
- Implement comprehensive monitoring
- Set up health checks for remote agents
- Use connection pooling for performance

### Multi-Agent Deployments
- Ensure authentication forwarding is tested
- Verify remote agent accessibility
- Monitor cross-agent communication
- Implement circuit breakers for remote calls

---

## Architecture Integration

The A2A implementation integrates with other system components:

- **Authentication System** (`src/auth/`) - Provides OAuth and bearer token validation
- **Agent Factory** (`src/agent_factory/`) - Manages remote agent connections
- **Agent Tools** (`src/tools/`) - Receive authentication context from A2A calls
- **Configuration** (`config/`) - Agent card and security scheme definitions

This A2A system provides the foundation for secure, scalable multi-agent orchestration with enterprise-grade authentication and monitoring capabilities.