"""
Authenticated Tool Base Class

This module provides a base class for creating tools that require user authentication.
"""

import time
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from datetime import datetime

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