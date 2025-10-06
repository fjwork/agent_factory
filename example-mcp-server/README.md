# Example MCP Server

This directory contains both a **legacy REST API server** and a **proper MCP server** that demonstrates how to create the server-side component that works with the MCP toolkit integration in the agent template.

## What This Is

This provides the **server-side component** - the actual MCP server that your ADK agent connects to using the `mcp_toolkit.py` in the agent template.

## Server Options

### 1. mcp_server.py (RECOMMENDED)
**Proper MCP Protocol Implementation**
- Uses FastMCP framework
- Implements correct MCP protocol over HTTP
- StreamableHTTP transport at `/mcp` endpoint
- JWT authentication support
- Compatible with Google ADK MCP toolkit

### 2. server.py (LEGACY)
**Simple REST API (for reference)**
- Basic Flask REST endpoints
- `/mcp/tools` and `/mcp/call` routes
- **Note**: This does NOT work with MCP toolkit due to protocol mismatch

## Architecture

```
┌─────────────────┐    MCP Protocol     ┌─────────────────┐
│   ADK Agent     │ ──────────────────→ │   MCP Server    │
│                 │    (JSON-RPC/HTTP)  │   (FastMCP)     │
│ mcp_toolkit.py  │ ←────────────────── │                 │
│ (Client)        │    Streaming HTTP   │ mcp_server.py   │
└─────────────────┘                     └─────────────────┘
```

## MCP Protocol (mcp_server.py)

The proper MCP server uses JSON-RPC over HTTP with streaming support at `/mcp` endpoint.

**Authentication:**
- JWT tokens in `X-Serverless-Authorization` header
- Automatic validation for all tool calls

**Available Tools:**
- `get_weather(location: str)` - Get weather data for a location
- `search_news(query: str)` - Search for news articles
- `health_check()` - Server health status
- `simple_test()` - Simple test tool without authentication

## Running the Proper MCP Server

```bash
# Install dependencies
pip install -r requirements.txt

# Run the MCP server (RECOMMENDED)
python mcp_server.py

# Server will start on http://localhost:8080
# MCP endpoint: http://localhost:8080/mcp
# Health check: Use MCP protocol to call health_check tool
```

## Legacy REST Server (server.py)

The legacy server provides REST endpoints but does NOT work with the MCP toolkit:

```bash
# Run legacy server (for reference only)
python server.py
```

## Integration with ADK Agent

1. **Start the MCP server**:
```bash
cd example-mcp-server/
python mcp_server.py
```

2. **Configure your ADK agent** with these environment variables:
```bash
# In agent-template/.env
MCP_SERVER_URL=http://localhost:8080
ENABLE_WEATHER_MCP=true
```

3. **Run your ADK agent** - it will automatically discover and use the tools from this server:
```bash
cd agent-template/
python src/agent.py
```

## Testing the Complete Setup

### Step 1: Start MCP Server
```bash
cd example-mcp-server/
python mcp_server.py
```

### Step 2: Test MCP Server Health
```bash
# The MCP server doesn't have a REST health endpoint
# Health checking is done via MCP protocol using the health_check tool
# You can test basic connectivity by checking if the server is running
ps aux | grep mcp_server
```

### Step 3: Start Agent and Test
```bash
# In another terminal
cd agent-template/
python src/agent.py

# Test weather tool with authentication
curl -X POST http://localhost:8001/ \
  -H "Authorization: Bearer test-token-123" \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": "test-weather-1",
    "method": "message/send",
    "params": {
      "context_id": "test-weather-1",
      "message": {
        "messageId": "weather-test",
        "role": "user",
        "parts": [{
          "text": "Get weather for San Francisco"
        }]
      }
    }
  }'
```

## Available Tools

### get_weather(location: str)
- Get weather data for a location
- Returns temperature, conditions, forecast

### search_news(query: str)
- Search for news articles on a topic
- Returns article summaries and sources

### health_check()
- Server health and status information
- No parameters required

### simple_test()
- Simple test tool without authentication for debugging
- No parameters required

## Authentication

This server validates JWT tokens sent by the ADK agent. The validation includes:

1. Token extraction from headers
2. JWT payload decoding (signature verification disabled for testing)
3. User information extraction
4. Request logging with user context

In production, implement proper JWT signature validation and token expiration checks.

## Extending the MCP Server

To add new tools to the MCP server:

1. **Add a tool function** with the `@server.tool()` decorator:
```python
@server.tool()
async def my_custom_tool(parameter: str) -> Dict[str, Any]:
    """Tool description here."""
    # Validate authentication
    headers = get_http_headers()
    user_info = validate_jwt_token(headers)
    if not user_info:
        return {"error": "Authentication required"}

    # Your tool logic here
    return {"result": "custom data"}
```

2. **Restart the server** - FastMCP automatically discovers new tools