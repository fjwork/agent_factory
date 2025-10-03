# Example MCP Server

This is an example MCP server that demonstrates how to create the server-side component that works with the MCP toolkit integration in the agent template.

## What This Is

This is the **missing piece** - the actual MCP server that your ADK agent connects to using the `mcp_toolkit.py` I created in the agent template.

## Architecture

```
┌─────────────────┐    HTTP/JWT     ┌─────────────────┐
│   ADK Agent     │ ──────────────→ │   MCP Server    │
│                 │                 │   (This Code)   │
│ mcp_toolkit.py  │ ←────────────── │                 │
│ (Client)        │    JSON Tools   │ server.py       │
└─────────────────┘                 └─────────────────┘
```

## Endpoints

### `GET /mcp/tools`
Returns available tools to the ADK agent.

**Headers Required:**
- `X-Serverless-Authorization: Bearer <jwt-token>`

**Response:**
```json
{
  "tools": [
    {
      "name": "get_weather",
      "description": "Get current weather for a location",
      "parameters": {
        "type": "object",
        "properties": {
          "location": {"type": "string"}
        }
      }
    }
  ]
}
```

### `POST /mcp/call`
Executes a tool with parameters.

**Headers Required:**
- `X-Serverless-Authorization: Bearer <jwt-token>`

**Request Body:**
```json
{
  "tool": "get_weather",
  "parameters": {
    "location": "San Francisco"
  }
}
```

**Response:**
```json
{
  "success": true,
  "result": {
    "location": "San Francisco",
    "temperature": "72°F",
    "condition": "Sunny"
  }
}
```

## Running the Server

```bash
# Install dependencies
pip install -r requirements.txt

# Run the server
python server.py

# Server will start on http://localhost:8080
```

## Integration with ADK Agent

1. **Start this MCP server** on port 8080
2. **Configure your ADK agent** to connect to it:

```bash
# In your agent environment
export MCP_SERVER_URL=http://localhost:8080
```

3. **Run your ADK agent** - it will automatically discover and use the tools from this server

## Available Tools

### get_weather
- **Description**: Get weather data for a location
- **Parameters**: location (string)
- **Example**: `{"location": "New York"}`

### search_news
- **Description**: Search for news articles
- **Parameters**: query (string)
- **Example**: `{"query": "AI technology"}`

## Authentication

This server validates JWT tokens sent by the ADK agent. In production, you should:

1. Properly validate JWT signatures
2. Check token expiration
3. Verify issuer and audience
4. Implement proper error handling

## Extending

To add your own tools:

1. **Define the tool** in the `get_tools()` response
2. **Implement the logic** in the `call_tool()` function
3. **Add the handler function** (like `get_weather_data()`)

Example:
```python
# In get_tools()
{
    "name": "my_custom_tool",
    "description": "My custom functionality",
    "parameters": {...}
}

# In call_tool()
elif tool_name == 'my_custom_tool':
    result = my_custom_tool_handler(parameters)

# Add the handler
def my_custom_tool_handler(parameters):
    # Your custom logic here
    return {"result": "custom data"}
```