"""
Authenticated tools and MCP toolkit for ADK agents.

This module provides:
- Tool registry system for centralized tool management
- MCP (Model Context Protocol) toolkit integration
- Traditional OAuth-authenticated tools
- Tool discovery and configuration
"""

from .authenticated_tool import AuthenticatedTool, AuthenticationError, ToolExecutionError
from .example_tool import ExampleTool, BearerTokenPrintTool
from .profile_tool import ProfileTool
from .tool_registry import (
    ToolRegistry,
    ToolConfig,
    MCPToolsetConfig,
    get_tool_registry,
    create_tools_from_registry
)
from .mcp_toolkit import (
    MCPToolsetWithAuth,
    create_mcp_auth_callback,
    create_weather_mcp_toolset
)

# Convenience function for quick tool setup
def create_authenticated_tools(config_dir=None, environment="development"):
    """
    Create all authenticated tools from registry.

    Args:
        config_dir: Configuration directory path
        environment: Environment name (development, staging, production)

    Returns:
        List of ADK FunctionTool instances
    """
    return create_tools_from_registry(config_dir, environment)

__all__ = [
    # Base classes
    "AuthenticatedTool",
    "AuthenticationError",
    "ToolExecutionError",

    # Example tools
    "ExampleTool",
    "BearerTokenPrintTool",
    "ProfileTool",

    # Tool registry
    "ToolRegistry",
    "ToolConfig",
    "MCPToolsetConfig",
    "get_tool_registry",
    "create_tools_from_registry",

    # MCP toolkit
    "MCPToolsetWithAuth",
    "create_mcp_auth_callback",
    "create_weather_mcp_toolset",

    # Convenience functions
    "create_authenticated_tools"
]