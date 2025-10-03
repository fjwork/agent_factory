"""
Simplified Authentication Module

Provides minimal authentication configuration and forwarding capabilities
without complex OAuth flows.
"""

from .auth_config import (
    AuthType,
    AuthContext,
    SimplifiedAuthConfig,
    load_auth_config,
    create_auth_context,
    extract_auth_from_request
)

from .auth_callback import (
    auth_forwarding_callback,
    set_auth_context,
    get_auth_context,
    clear_auth_context,
    create_auth_tool_context,
    AuthenticatedTool
)

__all__ = [
    # Auth config
    "AuthType",
    "AuthContext",
    "SimplifiedAuthConfig",
    "load_auth_config",
    "create_auth_context",
    "extract_auth_from_request",

    # Auth callback
    "auth_forwarding_callback",
    "set_auth_context",
    "get_auth_context",
    "clear_auth_context",
    "create_auth_tool_context",
    "AuthenticatedTool"
]