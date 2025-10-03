# Simplified Template

A streamlined ADK agent template with simplified authentication forwarding and HTTPS support, designed for secure inter-agent communication without complex OAuth flows.

## 🎯 Overview

This template provides:

- **Simplified Authentication** - Bearer token and API key forwarding without OAuth complexity
- **HTTPS Support** - Secure A2A communication with TLS/SSL
- **ADK Native Integration** - Leverages ADK's built-in authentication capabilities
- **Minimal Configuration** - Easy setup and deployment

## 🏗️ Architecture

### Key Differences from Full Template

| Feature | Full Template | Simplified Template |
|---------|---------------|-------------------|
| **OAuth Flows** | Device/Authorization Code | ❌ Removed |
| **Auth Providers** | Google, Azure, Okta | ❌ Simplified |
| **Auth Method** | Complex OAuth middleware | ✅ Bearer token forwarding |
| **Communication** | HTTP only | ✅ HTTPS with TLS |
| **Setup Complexity** | High (OAuth configuration) | ✅ Low (minimal config) |

### Components

```
simplified-template/
├── src/
│   ├── auth/                    # Simplified auth forwarding
│   │   ├── auth_config.py      # Minimal auth configuration
│   │   └── auth_callback.py    # ADK native auth forwarding
│   ├── a2a_server/             # HTTPS-enabled A2A server
│   ├── tools/                  # Example authenticated tools
│   └── agent.py               # Main agent entry point
├── config/                     # YAML configuration files
├── deployment/                 # SSL setup and deployment scripts
└── testing_scripts/           # Auth and HTTPS testing
```

## 🚀 Quick Start

### 1. Setup Environment

```bash
# Copy and configure environment
cp .env.example .env
# Edit .env with your settings

# Install dependencies
pip install -r requirements.txt
```

### 2. Basic Development (HTTP)

```bash
# Run in development mode
python src/agent.py
```

Agent will be available at `http://localhost:8000`

### 3. Production Setup (HTTPS)

```bash
# Generate SSL certificates
./deployment/ssl_setup.py --domain your-domain.com

# Configure environment for HTTPS
echo "HTTPS_ENABLED=true" >> .env
echo "SSL_CERT_FILE=./certs/your-domain.com.crt" >> .env
echo "SSL_KEY_FILE=./certs/your-domain.com.key" >> .env
echo "ENVIRONMENT=production" >> .env

# Start with HTTPS
python src/agent.py
```

Agent will be available at `https://your-domain.com:8000`

## 🔐 Authentication

### Supported Methods

1. **Bearer Token** (recommended)
   ```bash
   curl -H "Authorization: Bearer your-token" https://localhost:8000/auth/status
   ```

2. **API Key**
   ```bash
   curl -H "X-API-Key: your-api-key" https://localhost:8000/auth/status
   ```

3. **Basic Authentication**
   ```bash
   curl -u "username:password" https://localhost:8000/auth/status
   ```

### Auth Forwarding Flow

1. **Request Arrives** → Extract auth context from headers
2. **Set Context** → Store auth context for request lifecycle
3. **Forward to Tools** → Tools access auth via `get_auth_context()`
4. **Forward to Remote Agents** → Auth headers added to A2A calls
5. **Clean Up** → Auth context cleared after request

## 🛠️ Creating Authenticated Tools

```python
from auth import AuthenticatedTool

class MyTool(AuthenticatedTool):
    def __init__(self):
        super().__init__("my_tool", "Tool description")

    async def execute_with_context(self, param: str) -> dict:
        # Check if authenticated
        if not self.is_authenticated():
            return {"error": "Authentication required"}

        # Get auth context
        auth_context = self.get_auth_context()
        user_id = auth_context.user_id

        # Get headers for external API calls
        headers = self.get_auth_headers()

        # Your tool logic here
        return {"result": f"Authenticated as {user_id}"}
```

## 🔗 A2A Communication

### Setting Up Remote Agents

1. **Start Remote Agent**
   ```bash
   # Terminal 1: Remote agent
   cd remote-agent/
   python src/agent.py --port 8001
   ```

2. **Configure Root Agent**
   ```yaml
   # config/remote_agents.yaml
   remote_agents:
     - name: "remote_agent"
       url: "https://localhost:8001/a2a/remote_agent"
   ```

3. **Authentication is Forwarded Automatically**
   - Root agent extracts auth from incoming request
   - Auth headers automatically added to remote agent calls
   - Remote agent receives authentication context

### HTTPS Configuration

For secure A2A communication, both agents should use HTTPS:

```bash
# Generate certificates for both agents
./deployment/ssl_setup.py --domain agent1.example.com
./deployment/ssl_setup.py --domain agent2.example.com

# Configure remote agent URLs with HTTPS
remote_agents:
  - name: "secure_agent"
    url: "https://agent2.example.com:8001/a2a/secure_agent"
```

## 🧪 Testing

### Authentication Forwarding

```bash
# Test auth forwarding
./testing_scripts/test_auth_forwarding.sh

# Test with custom endpoint
HOST=your-domain.com PORT=8000 PROTOCOL=https ./testing_scripts/test_auth_forwarding.sh
```

### HTTPS Communication

```bash
# Test HTTPS setup
./testing_scripts/test_https.sh

# Test with custom ports
HTTP_PORT=8000 HTTPS_PORT=8443 ./testing_scripts/test_https.sh
```

### Manual Testing Examples

```bash
# Test authentication status
curl -H "Authorization: Bearer test-token" https://localhost:8000/auth/status

# Test A2A with auth
curl -X POST -H "Authorization: Bearer test-token" -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":"1","method":"message/send","params":{"message":{"messageId":"test","role":"user","parts":[{"text":"Show me my authentication info"}]}}}' \
  https://localhost:8000/

# Test tool execution
curl -X POST -H "Authorization: Bearer test-token" -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":"1","method":"message/send","params":{"message":{"messageId":"test","role":"user","parts":[{"text":"Validate my bearer token"}]}}}' \
  https://localhost:8000/
```

## 📋 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check and service status |
| `/.well-known/agent-card.json` | GET | Agent card for A2A discovery |
| `/auth/status` | GET | Authentication status check |
| `/` | POST | A2A protocol endpoint |

## 🔧 Configuration

### Environment Variables

```bash
# Agent settings
AGENT_NAME=SimplifiedAgent
MODEL_NAME=gemini-2.0-flash
ENVIRONMENT=development

# Server settings
HOST=0.0.0.0
PORT=8000

# HTTPS settings (production)
HTTPS_ENABLED=true
SSL_CERT_FILE=./certs/localhost.crt
SSL_KEY_FILE=./certs/localhost.key

# Development settings
CORS_ENABLED=true
LOG_LEVEL=INFO
```

### Authentication Configuration

Edit `config/auth_config.yaml`:

```yaml
auth:
  default_type: "bearer_token"
  require_https: true
  forward_headers: true
  allowed_types: ["bearer_token", "api_key"]
```

## 🔒 Security Features

### HTTPS/TLS
- **SSL/TLS Encryption** for all communication
- **Certificate Management** with automated setup
- **HTTPS Enforcement** in production mode
- **Security Headers** for enhanced protection

### Authentication
- **Bearer Token Forwarding** to tools and remote agents
- **Header Sanitization** for sensitive data
- **Secure Token Storage** in request context
- **No Persistent Secrets** (stateless design)

### Best Practices
- Use HTTPS in production
- Rotate bearer tokens regularly
- Validate tokens at the application level
- Monitor authentication logs
- Use strong SSL/TLS configurations

## 🚀 Deployment

### Local Development
```bash
cp .env.example .env
python src/agent.py
```

### Production (Manual)
```bash
./deployment/ssl_setup.py --domain your-domain.com --type letsencrypt --email your@email.com
ENVIRONMENT=production python src/agent.py
```

### Docker Deployment
```bash
# TODO: Add Dockerfile and docker-compose.yml
```

### Google Cloud Run
```bash
# TODO: Add Cloud Run deployment scripts
```

## 🔄 Migration from Full Template

1. **Remove OAuth Configuration** - No client secrets needed
2. **Update Auth Calls** - Use `get_auth_context()` instead of OAuth APIs
3. **Configure HTTPS** - Add SSL certificates and enable HTTPS
4. **Test Auth Forwarding** - Verify auth headers reach tools and remote agents

## 🐛 Troubleshooting

### Common Issues

**Auth context not available in tools:**
- Check if `auth_forwarding_callback` is set on agent
- Verify auth headers are present in request

**HTTPS certificate errors:**
- Regenerate certificates with correct domain
- Check certificate file permissions (600 for key, 644 for cert)
- Verify certificate hasn't expired

**Remote agent auth failures:**
- Ensure remote agent URL uses HTTPS
- Check if auth headers are being forwarded
- Verify remote agent can handle forwarded auth

### Debug Logging

```bash
LOG_LEVEL=DEBUG python src/agent.py
```

## 📚 Additional Resources

- [ADK Documentation](https://google.github.io/adk-docs/)
- [A2A Protocol Guide](https://google.github.io/adk-docs/a2a/)
- [SSL/TLS Best Practices](https://ssl-config.mozilla.org/)

---

**Next Steps:**
1. Customize tools for your use case
2. Set up production HTTPS certificates
3. Configure remote agents as needed
4. Deploy to your target environment