# Tool Registry and MCP Toolkit Guide

This guide explains how to use the new tool registry system and MCP toolkit integration in the agent template.

## Overview

The enhanced agent template now includes:

1. **Tool Registry System** - Centralized tool management and configuration
2. **MCP Toolkit Integration** - Support for Model Context Protocol toolsets
3. **Unified Authentication** - OAuth and JWT token management for both traditional and MCP tools

## Tool Registry System

### Configuration Files

#### `config/tool_registry.yaml`
Defines traditional authenticated tools:

```yaml
tools:
  example_tool:
    type: "authenticated"
    description: "Example OAuth-authenticated tool"
    enabled: true
    auth_required: true
    config:
      default_action: "get_user_info"
    environments:
      development:
        enabled: true
      production:
        enabled: true
```

#### `config/mcp_toolsets.yaml`
Defines MCP toolsets:

```yaml
mcp_toolsets:
  weather_toolset:
    url: "${MCP_SERVER_URL:http://localhost:8080}"
    description: "Weather forecast and information toolset"
    enabled: true
    timeout: 60
    auth_required: true
    auth_header: "X-Serverless-Authorization"
    token_refresh_threshold_mins: 15
```

### Using the Tool Registry

#### Basic Usage

```python
from tools import create_authenticated_tools

# Create all tools from registry
tools = create_authenticated_tools(config_dir="./config", environment="development")
```

#### Advanced Usage

```python
from tools import get_tool_registry, ToolRegistry

# Get registry instance
registry = get_tool_registry(config_dir="./config", environment="development")

# Create tools
registry.create_authenticated_tools()

# Get tool status
status = registry.get_tool_status()
print(f"Loaded {status['registered_tools']} tools")

# List available tools
available = registry.list_available_tools()
for name, info in available.items():
    print(f"- {name}: {info['description']}")
```

## MCP Toolkit Integration

### Features

- **Automatic JWT Token Management** - Handles token refresh and expiration
- **Tool Caching** - Improves performance by caching discovered tools
- **Authentication Header Injection** - Automatically adds auth headers to requests
- **Google Cloud Integration** - Uses Google Cloud credentials for authentication

### Creating MCP Toolsets

#### Using Configuration

```yaml
# In config/mcp_toolsets.yaml
my_custom_toolset:
  url: "https://my-mcp-server.com"
  description: "Custom MCP toolset"
  enabled: true
  auth_required: true
  auth_header: "Authorization"
  headers:
    User-Agent: "my-agent-client"
```

#### Programmatic Creation

```python
from tools.mcp_toolkit import MCPToolsetWithAuth

# Create MCP toolset
toolset = MCPToolsetWithAuth(
    name="my_toolset",
    url="https://my-mcp-server.com",
    timeout=60,
    auth_required=True,
    auth_header="X-Serverless-Authorization"
)

# Create weather toolset (convenience function)
from tools.mcp_toolkit import create_weather_mcp_toolset
weather_toolset = create_weather_mcp_toolset()
```

### Authentication Flow

1. **Token Request** - Automatically requests JWT tokens from Google Cloud
2. **Token Validation** - Checks token expiration before each request
3. **Token Refresh** - Refreshes tokens when they approach expiration
4. **Header Injection** - Adds authentication headers to MCP requests

### Monitoring and Debugging

```python
# Check cache status
cache_status = toolset.get_cache_status()
print(f"Tools cached: {cache_status['has_cached_tools']}")
print(f"Token valid: {cache_status['token_valid']}")

# Global cache status
from tools.mcp_toolkit import MCPToolsetWithAuth
global_status = MCPToolsetWithAuth.get_global_cache_status()
print(f"Total toolsets: {global_status['total_toolsets']}")

# Clear caches if needed
toolset.clear_cache()  # Clear single toolset
MCPToolsetWithAuth.clear_all_caches()  # Clear all caches
```

## Environment Configuration

### Required Environment Variables

```bash
# MCP Server Configuration
MCP_SERVER_URL=https://your-mcp-server.com
TOKEN_REFRESH_THRESHOLD_MINS=15

# Google Cloud Authentication (for JWT tokens)
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json

# Agent Configuration
AGENT_NAME=MyAgent
ENVIRONMENT=development
```

### Environment-Specific Settings

Tools can be configured differently per environment:

```yaml
weather_toolset:
  url: "http://localhost:8080"
  enabled: true
  environments:
    development:
      url: "http://localhost:8080"
      enabled: true
    staging:
      url: "https://staging-mcp.example.com"
      enabled: true
    production:
      url: "https://prod-mcp.example.com"
      enabled: true
```

## Agent Integration

The agent template automatically integrates both systems:

```python
# In src/agent.py (already implemented)
async def create_agent() -> Agent:
    # Load tools from registry
    tools = create_tools_from_registry(config_dir, environment)

    # Get MCP toolsets for auth callback
    tool_registry = get_tool_registry(config_dir, environment)
    mcp_toolsets = [tool for tool in tool_registry.tools.values()
                   if isinstance(tool, MCPToolsetWithAuth)]

    # Create combined auth callback
    mcp_auth_callback = create_mcp_auth_callback(mcp_toolsets)

    # Create agent with combined callback
    agent = Agent(
        tools=tools,
        before_agent_callback=combined_auth_callback
    )
```

## Best Practices

### Tool Organization

1. **Use Categories** - Group related tools in configuration
2. **Environment-Specific Enablement** - Disable debug tools in production
3. **Descriptive Names** - Use clear, descriptive tool names

### Security

1. **Token Management** - Tokens are automatically managed and refreshed
2. **Environment Variables** - Use environment variables for sensitive configuration
3. **HTTPS Only** - Use HTTPS URLs for production MCP servers

### Performance

1. **Tool Caching** - Tools are automatically cached for performance
2. **Connection Pooling** - Configure appropriate connection limits
3. **Timeouts** - Set reasonable timeouts for MCP requests

### Monitoring

1. **Logging** - Use appropriate log levels for different environments
2. **Health Checks** - Monitor MCP server health
3. **Cache Monitoring** - Monitor cache hit rates and token refresh frequency

## Troubleshooting

### Common Issues

#### Authentication Failures
```
ERROR: Failed to get ID token
```
- Check `GOOGLE_APPLICATION_CREDENTIALS` environment variable
- Verify service account has appropriate permissions
- Ensure MCP server URL is accessible

#### Tool Loading Failures
```
ERROR: Failed to create tool example_tool
```
- Check tool configuration in `tool_registry.yaml`
- Verify tool dependencies are available
- Check environment-specific overrides

#### MCP Connection Issues
```
ERROR: Failed to connect to MCP server
```
- Verify MCP server URL is correct and accessible
- Check network connectivity
- Verify authentication headers are correct

### Debug Mode

Enable debug logging for detailed information:

```bash
LOG_LEVEL=DEBUG python src/agent.py
```

This will show:
- Tool loading details
- Authentication token management
- MCP connection attempts
- Cache status updates

### Cache Management

If tools aren't updating, try clearing caches:

```python
# Clear specific toolset cache
toolset.clear_cache()

# Clear all caches
MCPToolsetWithAuth.clear_all_caches()

# Reload configurations
registry.reload_configurations()
```