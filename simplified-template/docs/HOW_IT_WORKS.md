# How the Simplified Template Works

This document explains the complete end-to-end flow of the simplified template in an easy-to-understand way.

## 🎯 Overview

The simplified template is like a **smart relay system** that:

1. **Receives requests** with authentication information
2. **Extracts and stores** that auth info temporarily
3. **Forwards the auth** to tools and remote agents automatically
4. **Processes the request** using authenticated services
5. **Cleans up** the auth info when done

Think of it like a **trusted messenger** that carries your ID card to different departments in a building, so you don't have to show it at every door.

## 🏗️ Architecture Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Client App    │───▶│ Simplified Agent │───▶│  Remote Agent   │
│                 │    │                 │    │                 │
│ Bearer Token:   │    │ 1. Extract Auth │    │ Receives Auth   │
│ "abc123..."     │    │ 2. Store Context│    │ Headers Auto    │
│                 │    │ 3. Forward Auth │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │ Authenticated   │
                       │ Tools           │
                       │                 │
                       │ Access Auth via │
                       │ get_auth_context│
                       └─────────────────┘
```

## 🔄 Complete Request Flow

Let's trace a request from start to finish:

### 1. **Client Sends Request**

```bash
curl -X POST \
  -H "Authorization: Bearer my-secret-token-123" \
  -H "X-User-ID: john.doe" \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": "1",
    "method": "message/send",
    "params": {
      "message": {
        "role": "user",
        "parts": [{"text": "Show me my authentication info"}]
      }
    }
  }' \
  https://localhost:8000/
```

**What happens here:**
- Client includes a Bearer token in the `Authorization` header
- Additional user info in `X-User-ID` header
- Sends an A2A protocol message to the agent

### 2. **Request Hits A2A Server**

The request arrives at our HTTPS-enabled A2A server:

```python
# src/a2a_server/server.py
class SimplifiedA2ARequestHandler(DefaultRequestHandler):
    async def handle_post(self, request: Request) -> Response:
        # Step 2a: Extract authentication from headers
        auth_context = extract_auth_from_request(request)

        # Step 2b: Store auth context for this request
        set_auth_context(auth_context)

        # Step 2c: Process the A2A request normally
        response = await super().handle_post(request)

        # Step 2d: Clean up after request
        clear_auth_context()
        return response
```

**What happens here:**
- Server extracts `Bearer my-secret-token-123` from `Authorization` header
- Creates an `AuthContext` object with the token and user info
- Stores it globally for this request (thread-safe)
- Proceeds with normal A2A processing

### 3. **Authentication Extraction**

```python
# src/auth/auth_config.py
def extract_auth_from_request(request) -> Optional[AuthContext]:
    auth_header = request.headers.get("Authorization", "")

    if auth_header.startswith("Bearer "):
        token = auth_header[7:]  # Remove "Bearer " prefix
        return create_auth_context(
            auth_type=AuthType.BEARER_TOKEN,
            token=token,  # "my-secret-token-123"
            user_id=request.headers.get("X-User-ID"),  # "john.doe"
            provider=request.headers.get("X-Auth-Provider", "unknown")
        )
```

**What happens here:**
- Looks for `Authorization: Bearer xyz` header
- Extracts just the token part: `my-secret-token-123`
- Gets additional user info from other headers
- Creates a structured `AuthContext` object

### 4. **ADK Agent Processing Begins**

The A2A protocol forwards the message to our ADK agent:

```python
# src/agent.py
agent = Agent(
    model="gemini-2.0-flash",
    name="SimplifiedAgent",
    tools=tools,
    sub_agents=remote_agents,
    before_agent_callback=auth_forwarding_callback  # 🔑 Key part!
)
```

**What happens here:**
- ADK starts processing the user's message
- **Before** doing anything else, it calls our `auth_forwarding_callback`
- This callback runs before the agent processes tools or remote agents

### 5. **Auth Forwarding Callback**

This is the **magic** that makes everything work:

```python
# src/auth/auth_callback.py
def auth_forwarding_callback(callback_context: CallbackContext):
    # Step 5a: Get the auth context we stored earlier
    auth_context = get_auth_context()

    if auth_context:
        # Step 5b: Forward to remote agents
        if agent.sub_agents:
            for sub_agent in agent.sub_agents:
                auth_headers = auth_context.to_headers()
                sub_agent._httpx_client.headers.update(auth_headers)

    # Auth context is now available to tools via get_auth_context()
```

**What happens here:**
- Retrieves the auth context we stored in step 2
- Converts it to HTTP headers: `{"Authorization": "Bearer my-secret-token-123", "X-User-ID": "john.doe"}`
- Updates **all remote agents'** HTTP clients with these headers
- Makes auth context available to tools through `get_auth_context()`

### 6. **Tool Execution with Auth**

When the agent decides to use a tool:

```python
# src/tools/example_authenticated_tool.py
class ExampleAuthenticatedTool(AuthenticatedTool):
    async def execute_with_context(self, action: str = "info"):
        # Step 6a: Get auth context automatically
        auth_context = self.get_auth_context()

        if not auth_context:
            return {"error": "No authentication available"}

        # Step 6b: Use auth info
        return {
            "authenticated": True,
            "user_id": auth_context.user_id,  # "john.doe"
            "token_present": auth_context.token is not None,
            "auth_type": auth_context.auth_type.value  # "bearer_token"
        }
```

**What happens here:**
- Tool calls `self.get_auth_context()` which retrieves our stored auth context
- Tool can access user ID, token, and other auth info
- Tool can make authenticated API calls using `self.get_auth_headers()`

### 7. **Remote Agent Communication**

If the agent needs to call a remote agent:

```python
# This happens automatically behind the scenes
remote_agent_call = {
    "url": "https://remote-agent:8001/a2a/remote_agent",
    "headers": {
        "Authorization": "Bearer my-secret-token-123",  # ✅ Auto-added
        "X-User-ID": "john.doe",                       # ✅ Auto-added
        "X-Auth-Type": "bearer_token",                 # ✅ Auto-added
        "Content-Type": "application/json"
    },
    "data": {...}  # A2A protocol message
}
```

**What happens here:**
- Remote agent receives the **exact same auth headers** as the original request
- Remote agent can use its own `extract_auth_from_request()` to get the auth context
- **Zero configuration** - auth forwarding just works!

### 8. **Response and Cleanup**

```python
# Back in the request handler
finally:
    clear_auth_context()  # Clean up auth context
```

**What happens here:**
- Request is complete, auth context is cleared
- Memory is cleaned up
- Ready for the next request

## 🔐 Authentication Context Object

The `AuthContext` is the heart of the system:

```python
@dataclass
class AuthContext:
    auth_type: AuthType          # "bearer_token", "api_key", etc.
    token: str                   # "my-secret-token-123"
    user_id: str                 # "john.doe"
    provider: str                # "my-auth-provider"
    headers: Dict[str, str]      # Additional headers
    metadata: Dict[str, Any]     # Extra data

    def to_headers(self) -> Dict[str, str]:
        """Convert to HTTP headers for forwarding"""
        return {
            "Authorization": f"Bearer {self.token}",
            "X-User-ID": self.user_id,
            "X-Auth-Type": self.auth_type.value,
            "X-Auth-Provider": self.provider
        }
```

This object travels through the entire request lifecycle, carrying all the auth information needed.

## 🔄 Request Lifecycle Summary

Here's the complete flow in simple terms:

```
1. 📨 Request arrives with Bearer token
2. 🔍 Server extracts auth info into AuthContext
3. 💾 AuthContext stored globally for this request
4. 🤖 ADK agent starts processing
5. 📡 Auth callback forwards auth to remote agents
6. 🛠️  Tools access auth via get_auth_context()
7. 🔗 Remote agents receive auth headers automatically
8. ✅ Request completes, auth context cleaned up
```

## 🛠️ How Tools Use Authentication

### Simple Tool Example

```python
class MyTool(AuthenticatedTool):
    def __init__(self):
        super().__init__("my_tool", "My custom tool")

    async def execute_with_context(self, query: str):
        # 1. Check if authenticated
        if not self.is_authenticated():
            return {"error": "Please provide authentication"}

        # 2. Get user info
        auth_context = self.get_auth_context()
        user_id = auth_context.user_id

        # 3. Make authenticated API call
        headers = self.get_auth_headers()
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"https://api.example.com/user/{user_id}/data",
                headers=headers  # Includes Bearer token automatically
            )

        return {"data": response.json()}
```

### What the Tool Gets

When `self.get_auth_headers()` is called, the tool receives:

```python
{
    "Authorization": "Bearer my-secret-token-123",
    "X-User-ID": "john.doe",
    "X-Auth-Type": "bearer_token",
    "X-Auth-Provider": "my-auth-provider"
}
```

Ready to use with any HTTP client!

## 🌐 HTTPS Communication

### Development vs Production

**Development (HTTP):**
```
Client ──HTTP──▶ Agent ──HTTP──▶ Remote Agent
```

**Production (HTTPS):**
```
Client ──HTTPS──▶ Agent ──HTTPS──▶ Remote Agent
       TLS 1.3         TLS 1.3
```

### SSL Certificate Setup

```bash
# Development: Self-signed certificate
./deployment/ssl_setup.py --domain localhost

# Production: Let's Encrypt certificate
./deployment/ssl_setup.py --domain myapp.com --type letsencrypt --email admin@myapp.com
```

### What HTTPS Provides

1. **Encryption**: All data (including Bearer tokens) encrypted in transit
2. **Integrity**: Prevents tampering with requests/responses
3. **Authentication**: Verifies server identity
4. **Trust**: Industry-standard security for production

## 🔍 Configuration Flow

### Environment Variables → YAML → Runtime

```
.env file:
AGENT_NAME=MyAgent
HTTPS_ENABLED=true
SSL_CERT_FILE=./certs/localhost.crt

↓

config/auth_config.yaml:
auth:
  default_type: "bearer_token"
  require_https: true

↓

Runtime:
SimplifiedAuthConfig(
  default_auth_type=AuthType.BEARER_TOKEN,
  require_https=True
)
```

### Server Configuration

```python
# Based on environment
if environment == "production" and cert_file and key_file:
    uvicorn_config = {
        "ssl_certfile": cert_file,
        "ssl_keyfile": key_file,
        "ssl_version": ssl.PROTOCOL_TLS_SERVER
    }
    # Results in HTTPS server
else:
    uvicorn_config = {"host": "0.0.0.0", "port": 8000}
    # Results in HTTP server
```

## 🧪 How Testing Works

### Auth Forwarding Test

```bash
# Test script sends request with Bearer token
curl -H "Authorization: Bearer test-token-123" \
     -H "X-User-ID: test-user" \
     https://localhost:8000/auth/status

# Server responds with:
{
  "authenticated": true,
  "auth_type": "bearer_token",
  "user_id": "test-user",
  "forwarding_enabled": true
}
```

### A2A Test

```bash
# Test script sends A2A message with auth
curl -X POST -H "Authorization: Bearer test-token" \
     -d '{"jsonrpc":"2.0","method":"message/send",...}' \
     https://localhost:8000/

# Agent processes message, forwards auth to tools/remote agents
# Tools receive auth context automatically
```

## 🔧 Error Handling

### What Happens When Things Go Wrong

**No Authentication:**
```python
auth_context = get_auth_context()  # Returns None
if not auth_context:
    return {"error": "Authentication required"}
```

**Invalid Token:**
```python
# Tool can implement validation
if not self.validate_token(auth_context.token):
    return {"error": "Invalid or expired token"}
```

**HTTPS Certificate Issues:**
```python
# Server logs error and falls back to HTTP in development
logger.warning("SSL certificate invalid, falling back to HTTP")
```

**Remote Agent Connection Failed:**
```python
# Auth headers still sent, but remote agent handles the failure
logger.error(f"Failed to connect to {remote_agent.url}")
```

## 🎯 Key Benefits of This Architecture

### 1. **Simplicity**
- No OAuth flows to configure
- No complex token storage
- No provider-specific code

### 2. **Security**
- HTTPS encryption for all communication
- Secure token forwarding
- No persistent token storage (stateless)

### 3. **Flexibility**
- Works with any Bearer token
- Supports multiple auth types (Bearer, API Key, Basic)
- Easy to extend for new auth methods

### 4. **Developer Experience**
- Tools automatically get auth context
- Remote agents automatically receive auth headers
- Zero configuration for basic setup

### 5. **Production Ready**
- Proper SSL/TLS support
- Security headers and middleware
- Comprehensive testing framework

## 🤔 Common Questions

**Q: Where is the auth context stored?**
A: In a global variable that's request-scoped. Each request gets its own auth context that's cleaned up when the request completes.

**Q: How do remote agents get the auth headers?**
A: The `auth_forwarding_callback` automatically updates each remote agent's HTTP client with auth headers before any calls are made.

**Q: What if I don't provide authentication?**
A: The system works fine without auth. Tools can check `if self.is_authenticated()` and handle unauthenticated requests appropriately.

**Q: Can I use custom authentication methods?**
A: Yes! Extend `extract_auth_from_request()` to handle custom auth headers, and add new `AuthType` values.

**Q: Is this production-ready?**
A: Yes! The template includes HTTPS/TLS, proper security headers, error handling, and comprehensive testing.

This architecture provides a perfect balance of simplicity, security, and functionality - making it easy to build authenticated agents without OAuth complexity while maintaining enterprise-grade security through HTTPS and proper auth forwarding! 🚀