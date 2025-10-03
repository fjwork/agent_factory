"""
Simplified Authentication Callback for Auth Forwarding

This module provides a simplified auth forwarding mechanism using ADK's native
callback system without complex OAuth flows.
"""

import logging
from typing import Optional, Dict, Any
from google.adk.agents.callback_context import CallbackContext
from google.genai import types

from .auth_config import AuthContext, extract_auth_from_request

logger = logging.getLogger(__name__)

# Global auth context store for the current request
_current_auth_context: Optional[AuthContext] = None


def set_auth_context(auth_context: Optional[AuthContext]) -> None:
    """Set the current authentication context for the request."""
    global _current_auth_context
    _current_auth_context = auth_context
    if auth_context:
        logger.debug(f"Set auth context: {auth_context.auth_type.value} for user {auth_context.user_id}")


def get_auth_context() -> Optional[AuthContext]:
    """Get the current authentication context."""
    return _current_auth_context


def clear_auth_context() -> None:
    """Clear the current authentication context."""
    global _current_auth_context
    _current_auth_context = None


def auth_forwarding_callback(callback_context: CallbackContext) -> Optional[types.Content]:
    """
    ADK callback for forwarding authentication context to remote agents and tools.

    This callback:
    1. Retrieves the current auth context set by the request handler
    2. Updates remote agents' HTTP clients with auth headers
    3. Ensures tools receive the auth context through ADK's native mechanisms
    """
    try:
        agent = callback_context._invocation_context.agent
        auth_context = get_auth_context()

        if not auth_context:
            logger.debug("No auth context available - agents will use default clients")
            return None

        logger.debug(f"Forwarding auth context: {auth_context.auth_type.value}")

        # Forward auth to remote agents via HTTP headers
        if hasattr(agent, 'sub_agents') and agent.sub_agents:
            _forward_auth_to_remote_agents(agent.sub_agents, auth_context)

        # Auth context will be available to tools via get_auth_context()
        # Tools should call get_auth_context() to access the current auth context

        return None

    except Exception as e:
        logger.error(f"Auth forwarding callback failed: {e}")
        return None


def _forward_auth_to_remote_agents(sub_agents, auth_context: AuthContext) -> None:
    """Forward authentication to remote agents via HTTP headers."""
    auth_headers = auth_context.to_headers()

    logger.debug(f"Forwarding auth to {len(sub_agents)} remote agents")

    for sub_agent in sub_agents:
        try:
            # Update RemoteA2aAgent HTTP client headers
            if hasattr(sub_agent, '_httpx_client') and sub_agent._httpx_client:
                sub_agent._httpx_client.headers.update(auth_headers)
                logger.info(f"✅ Updated {sub_agent.name} with auth headers")

            # Also try the newer pattern if ADK has updated
            elif hasattr(sub_agent, '_client') and sub_agent._client:
                if hasattr(sub_agent._client, 'headers'):
                    sub_agent._client.headers.update(auth_headers)
                    logger.info(f"✅ Updated {sub_agent.name} client with auth headers")

        except Exception as e:
            logger.error(f"Failed to update remote agent {getattr(sub_agent, 'name', 'unknown')}: {e}")


def create_auth_tool_context(auth_context: Optional[AuthContext] = None) -> Dict[str, Any]:
    """
    Create a context dictionary for tools that need authentication.

    This can be used by tools to access authentication information.
    """
    if auth_context is None:
        auth_context = get_auth_context()

    if not auth_context:
        return {}

    return {
        "auth_type": auth_context.auth_type.value,
        "token": auth_context.token,
        "user_id": auth_context.user_id,
        "provider": auth_context.provider,
        "headers": auth_context.to_headers(),
        "metadata": auth_context.metadata
    }


class AuthenticatedTool:
    """
    Base class for tools that need authentication context.

    Tools should inherit from this class to automatically receive
    auth context without complex setup.
    """

    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description

    def get_auth_context(self) -> Optional[AuthContext]:
        """Get the current authentication context for this tool."""
        return get_auth_context()

    def get_auth_headers(self) -> Dict[str, str]:
        """Get authentication headers for external API calls."""
        auth_context = self.get_auth_context()
        if auth_context:
            return auth_context.to_headers()
        return {}

    def is_authenticated(self) -> bool:
        """Check if the current request is authenticated."""
        auth_context = self.get_auth_context()
        return auth_context is not None and auth_context.token is not None

    def require_auth(self) -> None:
        """Raise an exception if not authenticated."""
        if not self.is_authenticated():
            raise ValueError("Authentication required for this operation")

    async def execute_with_context(self, *args, **kwargs):
        """
        Execute the tool with authentication context.

        Subclasses should override this method to implement their functionality.
        """
        raise NotImplementedError("Subclasses must implement execute_with_context")