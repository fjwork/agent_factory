"""
Tool Registry System

This module provides centralized tool management, discovery, and configuration
for the agent template. It supports both traditional AuthenticatedTool instances
and MCP toolkit integrations.
"""

import os
import yaml
import logging
from typing import Dict, List, Optional, Union, Any
from dataclasses import dataclass, field
from pathlib import Path

from google.adk.tools import FunctionTool
from google.adk.tools.base_tool import BaseTool
from .authenticated_tool import AuthenticatedTool
from .mcp_toolkit import MCPToolsetWithAuth

logger = logging.getLogger(__name__)


@dataclass
class ToolConfig:
    """Configuration for a single tool."""
    name: str
    type: str  # 'authenticated', 'mcp', 'function'
    description: Optional[str] = None
    enabled: bool = True
    config: Dict[str, Any] = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)
    auth_required: bool = False


@dataclass
class MCPToolsetConfig:
    """Configuration for MCP toolset."""
    name: str
    url: str
    timeout: int = 60
    auth_required: bool = True
    auth_header: str = "X-Serverless-Authorization"
    token_refresh_threshold_mins: int = 15
    enabled: bool = True
    description: Optional[str] = None
    headers: Dict[str, str] = field(default_factory=dict)


class ToolRegistry:
    """
    Centralized registry for managing agent tools.

    Supports:
    - Traditional AuthenticatedTool instances
    - MCP toolsets with authentication
    - Tool discovery and loading from configuration
    - Environment-specific tool enablement
    """

    def __init__(self, config_dir: Optional[str] = None, environment: str = "development"):
        self.config_dir = Path(config_dir) if config_dir else Path(__file__).parent.parent / "config"
        self.environment = environment
        self.tools: Dict[str, Union[AuthenticatedTool, MCPToolsetWithAuth]] = {}
        self.tool_configs: Dict[str, ToolConfig] = {}
        self.mcp_configs: Dict[str, MCPToolsetConfig] = {}

        # Load configurations
        self._load_tool_configurations()

    def _load_tool_configurations(self):
        """Load tool configurations from YAML files."""
        try:
            # Load main tool registry config
            registry_config_path = self.config_dir / "tool_registry.yaml"
            if registry_config_path.exists():
                with open(registry_config_path, 'r') as f:
                    config_data = yaml.safe_load(f)
                    self._parse_tool_configs(config_data)

            # Load MCP-specific configs
            mcp_config_path = self.config_dir / "mcp_toolsets.yaml"
            if mcp_config_path.exists():
                with open(mcp_config_path, 'r') as f:
                    mcp_data = yaml.safe_load(f)
                    self._parse_mcp_configs(mcp_data)

            logger.info(f"Loaded {len(self.tool_configs)} tool configs and {len(self.mcp_configs)} MCP configs")

        except Exception as e:
            logger.warning(f"Failed to load tool configurations: {e}")
            self._create_default_configs()

    def _parse_tool_configs(self, config_data: Dict[str, Any]):
        """Parse tool configurations from YAML data."""
        tools_section = config_data.get("tools", {})

        for tool_name, tool_data in tools_section.items():
            # Apply environment-specific overrides
            env_overrides = tool_data.get("environments", {}).get(self.environment, {})

            # Merge config with environment overrides
            merged_config = {**tool_data, **env_overrides}

            self.tool_configs[tool_name] = ToolConfig(
                name=tool_name,
                type=merged_config.get("type", "authenticated"),
                description=merged_config.get("description"),
                enabled=merged_config.get("enabled", True),
                config=merged_config.get("config", {}),
                dependencies=merged_config.get("dependencies", []),
                auth_required=merged_config.get("auth_required", False)
            )

    def _parse_mcp_configs(self, config_data: Dict[str, Any]):
        """Parse MCP toolset configurations from YAML data."""
        mcp_section = config_data.get("mcp_toolsets", {})

        for toolset_name, toolset_data in mcp_section.items():
            # Apply environment-specific overrides
            env_overrides = toolset_data.get("environments", {}).get(self.environment, {})

            # Merge config with environment overrides
            merged_config = {**toolset_data, **env_overrides}

            self.mcp_configs[toolset_name] = MCPToolsetConfig(
                name=toolset_name,
                url=merged_config["url"],
                timeout=merged_config.get("timeout", 60),
                auth_required=merged_config.get("auth_required", True),
                auth_header=merged_config.get("auth_header", "X-Serverless-Authorization"),
                token_refresh_threshold_mins=merged_config.get("token_refresh_threshold_mins", 15),
                enabled=merged_config.get("enabled", True),
                description=merged_config.get("description"),
                headers=merged_config.get("headers", {})
            )

    def _create_default_configs(self):
        """Create default tool configurations if none exist."""
        self.tool_configs = {
            "example_tool": ToolConfig(
                name="example_tool",
                type="authenticated",
                description="Example OAuth-authenticated tool",
                enabled=True,
                auth_required=True
            ),
            "bearer_token_print_tool": ToolConfig(
                name="bearer_token_print_tool",
                type="authenticated",
                description="Bearer token testing tool",
                enabled=True,
                auth_required=True
            )
        }

        # Default MCP config (if environment variables are set)
        mcp_url = os.getenv("MCP_SERVER_URL")
        if mcp_url:
            self.mcp_configs["default_mcp"] = MCPToolsetConfig(
                name="default_mcp",
                url=mcp_url,
                description="Default MCP toolset from environment"
            )

    def register_tool(self, tool: Union[AuthenticatedTool, MCPToolsetWithAuth]):
        """Register a tool instance in the registry."""
        tool_name = getattr(tool, 'name', None) or getattr(tool, '_tool_set_name', None)
        if tool_name:
            self.tools[tool_name] = tool
            logger.info(f"Registered tool: {tool_name}")
        else:
            logger.warning(f"Tool registration failed: no name found for {type(tool)}")

    def get_tool(self, name: str) -> Optional[Union[AuthenticatedTool, MCPToolsetWithAuth]]:
        """Get a registered tool by name."""
        return self.tools.get(name)

    def list_available_tools(self) -> Dict[str, Dict[str, Any]]:
        """List all available tools with their configurations."""
        available = {}

        # Traditional tools
        for name, config in self.tool_configs.items():
            if config.enabled:
                available[name] = {
                    "type": config.type,
                    "description": config.description,
                    "auth_required": config.auth_required,
                    "registered": name in self.tools
                }

        # MCP toolsets
        for name, config in self.mcp_configs.items():
            if config.enabled:
                available[name] = {
                    "type": "mcp",
                    "description": config.description,
                    "url": config.url,
                    "auth_required": config.auth_required,
                    "registered": name in self.tools
                }

        return available

    def create_authenticated_tools(self) -> List[Union[AuthenticatedTool, MCPToolsetWithAuth]]:
        """Create and register all enabled tools."""
        tools = []

        # Create traditional authenticated tools
        for name, config in self.tool_configs.items():
            if config.enabled:
                try:
                    tool = self._create_authenticated_tool(name, config)
                    if tool:
                        self.register_tool(tool)
                        tools.append(tool)
                except Exception as e:
                    logger.error(f"Failed to create tool {name}: {e}")

        # Create MCP toolsets
        for name, config in self.mcp_configs.items():
            if config.enabled:
                try:
                    toolset = self._create_mcp_toolset(name, config)
                    if toolset:
                        self.register_tool(toolset)
                        tools.append(toolset)
                except Exception as e:
                    logger.error(f"Failed to create MCP toolset {name}: {e}")

        logger.info(f"Created {len(tools)} tools from registry")
        return tools

    def _create_authenticated_tool(self, name: str, config: ToolConfig) -> Optional[AuthenticatedTool]:
        """Create an authenticated tool instance."""
        if config.type == "authenticated":
            # Import here to avoid circular imports
            if name == "example_tool":
                from .example_tool import ExampleTool
                return ExampleTool()
            elif name == "bearer_token_print_tool":
                from .example_tool import BearerTokenPrintTool
                return BearerTokenPrintTool()
            else:
                logger.warning(f"Unknown authenticated tool: {name}")
                return None
        else:
            logger.warning(f"Unsupported tool type: {config.type}")
            return None

    def _create_mcp_toolset(self, name: str, config: MCPToolsetConfig) -> Optional[MCPToolsetWithAuth]:
        """Create an MCP toolset instance."""
        try:
            return MCPToolsetWithAuth(
                name=name,
                url=config.url,
                timeout=config.timeout,
                auth_required=config.auth_required,
                auth_header=config.auth_header,
                token_refresh_threshold_mins=config.token_refresh_threshold_mins,
                headers=config.headers
            )
        except Exception as e:
            logger.error(f"Failed to create MCP toolset {name}: {e}")
            return None

    def get_adk_function_tools(self) -> List[FunctionTool]:
        """Convert registered tools to ADK FunctionTool instances."""
        function_tools = []

        for tool_name, tool in self.tools.items():
            try:
                if isinstance(tool, AuthenticatedTool):
                    # Convert AuthenticatedTool to FunctionTool
                    function_tool = FunctionTool(tool.execute_with_context)
                    function_tools.append(function_tool)
                elif isinstance(tool, MCPToolsetWithAuth):
                    # MCP toolsets are already BaseTool instances
                    function_tools.append(tool)
                else:
                    logger.warning(f"Unknown tool type for {tool_name}: {type(tool)}")

            except Exception as e:
                logger.error(f"Failed to convert tool {tool_name} to FunctionTool: {e}")

        return function_tools

    def reload_configurations(self):
        """Reload configurations from files."""
        logger.info("Reloading tool configurations...")
        self.tool_configs.clear()
        self.mcp_configs.clear()
        self._load_tool_configurations()

    def get_tool_status(self) -> Dict[str, Any]:
        """Get status information for all tools."""
        status = {
            "total_configs": len(self.tool_configs) + len(self.mcp_configs),
            "registered_tools": len(self.tools),
            "enabled_tools": sum(1 for c in self.tool_configs.values() if c.enabled) +
                            sum(1 for c in self.mcp_configs.values() if c.enabled),
            "environment": self.environment,
            "config_dir": str(self.config_dir),
            "tools": {}
        }

        # Add individual tool status
        for name, config in self.tool_configs.items():
            status["tools"][name] = {
                "type": config.type,
                "enabled": config.enabled,
                "registered": name in self.tools,
                "auth_required": config.auth_required
            }

        for name, config in self.mcp_configs.items():
            status["tools"][name] = {
                "type": "mcp",
                "enabled": config.enabled,
                "registered": name in self.tools,
                "url": config.url,
                "auth_required": config.auth_required
            }

        return status


# Global registry instance (singleton pattern)
_global_registry: Optional[ToolRegistry] = None


def get_tool_registry(config_dir: Optional[str] = None, environment: str = "development") -> ToolRegistry:
    """Get the global tool registry instance."""
    global _global_registry

    if _global_registry is None:
        _global_registry = ToolRegistry(config_dir, environment)

    return _global_registry


def create_tools_from_registry(config_dir: Optional[str] = None, environment: str = "development") -> List[FunctionTool]:
    """Convenience function to create all tools from registry."""
    registry = get_tool_registry(config_dir, environment)
    registry.create_authenticated_tools()
    return registry.get_adk_function_tools()