# Simplified Template Setup Guide

This guide walks you through setting up the simplified ADK agent template with auth forwarding and HTTPS support.

## Prerequisites

- Python 3.11 or later
- OpenSSL (for SSL certificate generation)
- curl and jq (for testing)

## Step-by-Step Setup

### 1. Environment Setup

```bash
# Clone or copy the simplified template
cp -r simplified-template/ my-agent/
cd my-agent/

# Install dependencies
pip install -r requirements.txt

# Copy environment configuration
cp .env.example .env
```

### 2. Basic Configuration

Edit `.env` file:

```bash
# Basic settings
AGENT_NAME=MySimplifiedAgent
MODEL_NAME=gemini-2.0-flash
ENVIRONMENT=development

# Server settings
HOST=0.0.0.0
PORT=8000

# Enable debug logging for development
LOG_LEVEL=DEBUG
```

### 3. Development Testing (HTTP)

```bash
# Start the agent in development mode
python src/agent.py
```

The agent will be available at `http://localhost:8000`

**Test basic functionality:**

```bash
# Health check
curl http://localhost:8000/health

# Agent card
curl http://localhost:8000/.well-known/agent-card.json

# Test auth forwarding
curl -H "Authorization: Bearer test-token-123" \
     -H "X-User-ID: test-user" \
     http://localhost:8000/auth/status
```

### 4. Production HTTPS Setup

#### Option A: Self-Signed Certificates (Development/Testing)

```bash
# Generate self-signed certificate
./deployment/ssl_setup.py --domain localhost --days 365

# Configure HTTPS in .env
echo "HTTPS_ENABLED=true" >> .env
echo "SSL_CERT_FILE=./certs/localhost.crt" >> .env
echo "SSL_KEY_FILE=./certs/localhost.key" >> .env
echo "ENVIRONMENT=production" >> .env

# Start with HTTPS
python src/agent.py
```

#### Option B: Let's Encrypt Certificates (Production)

```bash
# Generate Let's Encrypt certificate
sudo ./deployment/ssl_setup.py --domain your-domain.com --type letsencrypt --email your@email.com

# Configure HTTPS in .env
echo "HTTPS_ENABLED=true" >> .env
echo "SSL_CERT_FILE=/etc/letsencrypt/live/your-domain.com/fullchain.pem" >> .env
echo "SSL_KEY_FILE=/etc/letsencrypt/live/your-domain.com/privkey.pem" >> .env
echo "ENVIRONMENT=production" >> .env

# Start with HTTPS
python src/agent.py
```

### 5. Authentication Testing

Run comprehensive auth tests:

```bash
# Test authentication forwarding
./testing_scripts/test_auth_forwarding.sh

# Test HTTPS communication
./testing_scripts/test_https.sh
```

### 6. Custom Tool Development

Create your own authenticated tool:

```python
# src/tools/my_custom_tool.py
from auth import AuthenticatedTool
import httpx

class MyCustomTool(AuthenticatedTool):
    def __init__(self):
        super().__init__(
            name="my_custom_tool",
            description="Custom tool that uses authentication"
        )

    async def execute_with_context(self, action: str) -> dict:
        # Require authentication
        self.require_auth()

        # Get auth context
        auth_context = self.get_auth_context()

        # Make authenticated API call
        headers = self.get_auth_headers()

        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://api.example.com/data",
                headers=headers
            )

        return {
            "user_id": auth_context.user_id,
            "api_response": response.json()
        }
```

Add to agent:

```python
# src/agent.py
from tools.my_custom_tool import MyCustomTool

def create_authenticated_tools():
    my_tool = MyCustomTool()
    return [
        FunctionTool(my_tool.execute_with_context),
        # ... other tools
    ]
```

## Configuration Options

### Authentication Configuration

Edit `config/auth_config.yaml`:

```yaml
auth:
  # Default auth type for incoming requests
  default_type: "bearer_token"  # or "api_key", "basic_auth"

  # Require HTTPS in production
  require_https: true

  # Forward auth headers to remote agents
  forward_headers: true

  # Allowed authentication types
  allowed_types:
    - "bearer_token"
    - "api_key"
    - "basic_auth"
```

### Agent Configuration

Edit `config/agent_config.yaml`:

```yaml
agent:
  name: "${AGENT_NAME:MyAgent}"
  description: "My custom simplified agent"

server:
  host: "${HOST:0.0.0.0}"
  port: "${PORT:8000}"

  https:
    enabled: "${HTTPS_ENABLED:false}"
    cert_file: "${SSL_CERT_FILE:}"
    key_file: "${SSL_KEY_FILE:}"
```

## Remote Agent Setup

### 1. Create Remote Agent

```bash
# Copy template for remote agent
cp -r simplified-template/ remote-agent/
cd remote-agent/

# Configure for different port
echo "PORT=8001" >> .env
echo "AGENT_NAME=RemoteAgent" >> .env

# Start remote agent
python src/agent.py
```

### 2. Configure Root Agent for A2A

Create `config/remote_agents.yaml`:

```yaml
remote_agents:
  - name: "remote_agent"
    description: "Remote specialized agent"
    url: "https://localhost:8001/a2a/remote_agent"
    capabilities: ["data_processing"]
```

### 3. Test A2A Communication

```bash
# Test delegation to remote agent
curl -X POST -H "Authorization: Bearer test-token" \
     -H "Content-Type: application/json" \
     -d '{
       "jsonrpc": "2.0",
       "id": "1",
       "method": "message/send",
       "params": {
         "message": {
           "messageId": "test-delegation",
           "role": "user",
           "parts": [{
             "text": "Delegate this task to the remote agent"
           }]
         }
       }
     }' \
     https://localhost:8000/
```

## Deployment Options

### Local Production

```bash
# Use production environment
ENVIRONMENT=production python src/agent.py
```

### Systemd Service

Create `/etc/systemd/system/simplified-agent.service`:

```ini
[Unit]
Description=Simplified ADK Agent
After=network.target

[Service]
Type=simple
User=agent
WorkingDirectory=/path/to/simplified-template
Environment=ENVIRONMENT=production
ExecStart=/usr/bin/python3 src/agent.py
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl enable simplified-agent
sudo systemctl start simplified-agent
```

### Docker Deployment

Create `Dockerfile`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8000
CMD ["python", "src/agent.py"]
```

Build and run:

```bash
docker build -t simplified-agent .
docker run -p 8000:8000 -e ENVIRONMENT=production simplified-agent
```

## Monitoring and Logs

### Health Monitoring

```bash
# Basic health check
curl https://localhost:8000/health

# Detailed auth status
curl -H "Authorization: Bearer test-token" \
     https://localhost:8000/auth/status
```

### Log Analysis

```bash
# View logs with timestamp
python src/agent.py 2>&1 | tee agent.log

# Monitor authentication events
grep "auth" agent.log

# Monitor HTTPS activity
grep -i "ssl\|tls\|https" agent.log
```

## Troubleshooting

### Common Issues

1. **Port already in use:**
   ```bash
   # Check what's using the port
   lsof -i :8000

   # Use different port
   PORT=8080 python src/agent.py
   ```

2. **SSL certificate errors:**
   ```bash
   # Verify certificate
   openssl x509 -in ./certs/localhost.crt -text -noout

   # Check key permissions
   ls -la ./certs/localhost.key  # Should be 600
   ```

3. **Auth context not available:**
   ```bash
   # Enable debug logging
   LOG_LEVEL=DEBUG python src/agent.py

   # Check auth callback is registered
   grep "auth_forwarding_callback" src/agent.py
   ```

4. **Remote agent connection failed:**
   ```bash
   # Test remote agent directly
   curl https://localhost:8001/health

   # Check URL in configuration
   cat config/remote_agents.yaml
   ```

### Debug Commands

```bash
# Test SSL connection
openssl s_client -connect localhost:8000 -servername localhost

# Verify auth headers
curl -v -H "Authorization: Bearer test" https://localhost:8000/auth/status

# Test A2A protocol
curl -X POST -H "Content-Type: application/json" \
     -d '{"jsonrpc":"2.0","id":"1","method":"ping"}' \
     https://localhost:8000/
```

## Next Steps

1. **Customize for your use case**
   - Modify tools in `src/tools/`
   - Update agent instructions
   - Configure remote agents

2. **Production deployment**
   - Set up proper SSL certificates
   - Configure monitoring
   - Set up log aggregation

3. **Security hardening**
   - Implement token validation
   - Add rate limiting
   - Configure firewall rules

4. **Integration**
   - Connect to external APIs
   - Set up webhook endpoints
   - Integrate with existing systems