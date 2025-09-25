"""
Authenticated Tool Base Class

This module provides a base class for creating tools that require user authentication.
"""

import time
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from datetime import datetime

try:
    from google.adk.tools import ToolContext
except ImportError:
    # For environments where ADK is not available
    ToolContext = None

logger = logging.getLogger(__name__)


class AuthenticatedTool(ABC):
    """Base class for tools that require user authentication."""

    def __init__(self, name: str, description: Optional[str] = None):
        self.name = name
        self.description = description or f"Authenticated tool: {name}"

    @abstractmethod
    async def execute_authenticated(self, user_context: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """
        Execute the tool with authenticated user context.

        Args:
            user_context: Dictionary containing user authentication information
                - user_id: Unique user identifier
                - provider: OAuth provider name
                - user_info: User profile information
                - token: Access token information
            **kwargs: Tool-specific parameters

        Returns:
            Dictionary containing tool execution result

        Raises:
            AuthenticationError: If user context is invalid
            ToolExecutionError: If tool execution fails
        """
        pass

    async def execute_with_context(self, tool_context, **kwargs) -> Dict[str, Any]:
        """
        Execute tool using ADK ToolContext for user authentication.

        This method extracts OAuth context from ADK session state and calls execute_authenticated.

        Args:
            tool_context: ADK ToolContext with session state
            **kwargs: Tool-specific parameters

        Returns:
            Tool execution result

        Raises:
            AuthenticationError: If user context is invalid or missing
            ToolExecutionError: If tool execution fails
        """
        if ToolContext is None:
            raise AuthenticationError("ADK ToolContext not available - ensure google.adk is installed")

        # Extract OAuth context from session state
        user_context = {
            "user_id": tool_context.state.get("oauth_user_id"),
            "provider": tool_context.state.get("oauth_provider"),
            "user_info": tool_context.state.get("oauth_user_info", {}),
            "token": tool_context.state.get("oauth_token")
        }

        # If session state doesn't have OAuth context, try global registry fallback
        if not user_context["user_id"] or not user_context["token"]:
            # Import here to avoid circular imports
            try:
                from agent_a2a.handlers import AuthenticatedRequestHandler

                # Check if there's OAuth context in the global registry
                if hasattr(AuthenticatedRequestHandler, '_oauth_registry'):
                    registry = AuthenticatedRequestHandler._oauth_registry
                    # Find any authenticated user (in practice there should be only one at a time)
                    for user_id, oauth_context in registry.items():
                        if oauth_context.get("oauth_authenticated"):
                            # Normalize the context to ensure compatibility
                            user_context = {
                                "user_id": oauth_context.get("oauth_user_id"),
                                "oauth_user_id": oauth_context.get("oauth_user_id"),
                                "provider": oauth_context.get("oauth_provider"),
                                "oauth_provider": oauth_context.get("oauth_provider"),
                                "user_info": oauth_context.get("oauth_user_info", {}),
                                "oauth_user_info": oauth_context.get("oauth_user_info", {}),
                                "token": oauth_context.get("oauth_token"),
                                "oauth_token": oauth_context.get("oauth_token")
                            }
                            logger.info(f"Using global registry OAuth context for user {user_id}")
                            break
            except ImportError:
                pass

        # Validate that we have required authentication context
        if not user_context.get("user_id"):
            raise AuthenticationError("No user ID found in session state or global registry")

        if not user_context.get("token"):
            raise AuthenticationError("No OAuth token found in session state or global registry")

        logger.debug(f"Executing tool {self.name} with OAuth context for user {user_context['user_id']}")

        # Call the authenticated execution method
        return await self.execute_authenticated(user_context, **kwargs)

    def validate_user_context(self, user_context: Dict[str, Any]) -> bool:
        """
        Validate that user context contains required authentication information.

        Args:
            user_context: User authentication context

        Returns:
            True if valid, False otherwise
        """
        required_fields = ["user_id", "provider"]

        for field in required_fields:
            if field not in user_context:
                logger.error(f"Missing required field in user context: {field}")
                return False

        return True

    def get_user_id(self, user_context: Dict[str, Any]) -> Optional[str]:
        """Extract user ID from context."""
        return user_context.get("user_id")

    def get_provider(self, user_context: Dict[str, Any]) -> Optional[str]:
        """Extract OAuth provider from context."""
        return user_context.get("provider")

    def get_user_info(self, user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Extract user profile information from context."""
        return user_context.get("user_info", {})

    def get_access_token(self, user_context: Dict[str, Any]) -> Optional[str]:
        """Extract access token from context."""
        token_data = user_context.get("token")
        if token_data and hasattr(token_data, 'access_token'):
            return token_data.access_token
        return None

    def _get_timestamp(self) -> str:
        """Get current timestamp as ISO string."""
        return datetime.utcnow().isoformat() + "Z"

    def _log_tool_execution(self, user_context: Dict[str, Any], action: str, details: Optional[Dict[str, Any]] = None):
        """Log tool execution for audit purposes."""
        user_id = self.get_user_id(user_context)
        provider = self.get_provider(user_context)

        log_data = {
            "tool": self.name,
            "user_id": user_id,
            "provider": provider,
            "action": action,
            "timestamp": self._get_timestamp()
        }

        if details:
            log_data["details"] = details

        logger.info(f"Tool execution: {log_data}")

    async def fetch_real_user_info(self, user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Fetch real user information from OAuth provider API."""
        access_token = self.get_access_token(user_context)
        provider = self.get_provider(user_context)

        if not access_token:
            logger.warning("No access token available, using cached user info")
            return self.get_user_info(user_context)

        try:
            if provider == "google":
                return await self._fetch_google_user_info(access_token)
            else:
                logger.warning(f"Unsupported provider '{provider}', using cached user info")
                return self.get_user_info(user_context)

        except Exception as e:
            logger.warning(f"Failed to fetch real user info from {provider}: {e}, using cached data")
            return self.get_user_info(user_context)

    async def _fetch_google_user_info(self, access_token: str) -> Dict[str, Any]:
        """Fetch user information from Google UserInfo API."""
        try:
            import httpx
        except ImportError:
            raise ToolExecutionError("httpx is required for OAuth provider API calls. Install with: pip install httpx")

        url = "https://www.googleapis.com/oauth2/v2/userinfo"
        headers = {"Authorization": f"Bearer {access_token}"}

        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers, timeout=10.0)

            if response.status_code == 200:
                user_data = response.json()
                logger.info(f"Successfully fetched real user info from Google for: {user_data.get('email', 'unknown')}")
                return user_data
            else:
                error_msg = f"Google UserInfo API failed: {response.status_code} - {response.text}"
                logger.error(error_msg)
                raise ToolExecutionError(error_msg)


class AuthenticationError(Exception):
    """Raised when authentication fails or is invalid."""
    pass


class ToolExecutionError(Exception):
    """Raised when tool execution fails."""
    pass


# Example implementation
class ExampleAPITool(AuthenticatedTool):
    """Example tool that makes authenticated API calls."""

    def __init__(self):
        super().__init__(
            name="example_api_tool",
            description="Makes authenticated API calls to external services"
        )

    async def execute_authenticated(
        self,
        user_context: Dict[str, Any],
        endpoint: str,
        method: str = "GET",
        data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Make an authenticated API call.

        Args:
            user_context: User authentication context
            endpoint: API endpoint URL
            method: HTTP method (GET, POST, etc.)
            data: Request data for POST/PUT requests

        Returns:
            API response data
        """
        if not self.validate_user_context(user_context):
            raise AuthenticationError("Invalid user context")

        access_token = self.get_access_token(user_context)
        if not access_token:
            raise AuthenticationError("No access token available")

        self._log_tool_execution(
            user_context,
            "api_call",
            {"endpoint": endpoint, "method": method}
        )

        try:
            # Import here to avoid dependency issues if httpx not installed
            import httpx

            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }

            async with httpx.AsyncClient() as client:
                if method.upper() == "GET":
                    response = await client.get(endpoint, headers=headers)
                elif method.upper() == "POST":
                    response = await client.post(endpoint, headers=headers, json=data)
                elif method.upper() == "PUT":
                    response = await client.put(endpoint, headers=headers, json=data)
                elif method.upper() == "DELETE":
                    response = await client.delete(endpoint, headers=headers)
                else:
                    raise ToolExecutionError(f"Unsupported HTTP method: {method}")

                response.raise_for_status()

                return {
                    "success": True,
                    "status_code": response.status_code,
                    "data": response.json() if response.content else None,
                    "timestamp": self._get_timestamp()
                }

        except Exception as e:
            error_msg = f"API call failed: {e}"
            logger.error(error_msg)
            raise ToolExecutionError(error_msg)


class UserProfileTool(AuthenticatedTool):
    """Tool for accessing user profile information."""

    def __init__(self):
        super().__init__(
            name="user_profile_tool",
            description="Retrieves and manages user profile information"
        )

    async def execute_authenticated(
        self,
        user_context: Dict[str, Any],
        action: str = "get",
        profile_fields: Optional[list] = None
    ) -> Dict[str, Any]:
        """
        Access user profile information.

        Args:
            user_context: User authentication context
            action: Action to perform (get, update)
            profile_fields: Specific fields to retrieve

        Returns:
            User profile data
        """
        if not self.validate_user_context(user_context):
            raise AuthenticationError("Invalid user context")

        user_info = self.get_user_info(user_context)
        user_id = self.get_user_id(user_context)
        provider = self.get_provider(user_context)

        self._log_tool_execution(
            user_context,
            f"profile_{action}",
            {"fields": profile_fields}
        )

        if action == "get":
            # Filter profile fields if specified
            if profile_fields:
                filtered_info = {
                    field: user_info.get(field)
                    for field in profile_fields
                    if field in user_info
                }
            else:
                filtered_info = user_info

            return {
                "success": True,
                "user_id": user_id,
                "provider": provider,
                "profile": filtered_info,
                "timestamp": self._get_timestamp()
            }

        else:
            raise ToolExecutionError(f"Unsupported action: {action}")


# Factory function to create tool instances
def create_authenticated_tool(tool_type: str, **kwargs) -> AuthenticatedTool:
    """
    Factory function to create authenticated tool instances.

    Args:
        tool_type: Type of tool to create
        **kwargs: Tool-specific configuration

    Returns:
        Authenticated tool instance
    """
    if tool_type == "api":
        return ExampleAPITool()
    elif tool_type == "profile":
        return UserProfileTool()
    else:
        raise ValueError(f"Unknown tool type: {tool_type}")