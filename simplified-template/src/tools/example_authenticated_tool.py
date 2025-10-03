"""
Example Authenticated Tool

Demonstrates how to create tools that use the simplified auth forwarding mechanism.
"""

import logging
from typing import Dict, Any, Optional
from google.adk.tools import FunctionTool

from auth import AuthenticatedTool, get_auth_context

logger = logging.getLogger(__name__)


class ExampleAuthenticatedTool(AuthenticatedTool):
    """Example tool that demonstrates authentication context usage."""

    def __init__(self):
        super().__init__(
            name="example_authenticated_tool",
            description="Example tool that demonstrates auth context forwarding"
        )

    async def execute_with_context(self, action: str = "info") -> Dict[str, Any]:
        """
        Execute the tool with authentication context.

        Args:
            action: Action to perform ("info", "test", "headers")

        Returns:
            Dictionary with tool execution results
        """
        try:
            auth_context = self.get_auth_context()

            if action == "info":
                return await self._get_auth_info()
            elif action == "test":
                return await self._test_authenticated_request()
            elif action == "headers":
                return await self._get_auth_headers()
            else:
                return {
                    "error": f"Unknown action: {action}",
                    "available_actions": ["info", "test", "headers"]
                }

        except Exception as e:
            logger.error(f"Tool execution failed: {e}")
            return {
                "error": str(e),
                "tool": self.name
            }

    async def _get_auth_info(self) -> Dict[str, Any]:
        """Get authentication information."""
        auth_context = self.get_auth_context()

        if not auth_context:
            return {
                "authenticated": False,
                "message": "No authentication context available"
            }

        return {
            "authenticated": True,
            "auth_type": auth_context.auth_type.value,
            "user_id": auth_context.user_id,
            "provider": auth_context.provider,
            "has_token": auth_context.token is not None,
            "metadata": auth_context.metadata
        }

    async def _test_authenticated_request(self) -> Dict[str, Any]:
        """Test making an authenticated request."""
        if not self.is_authenticated():
            return {
                "authenticated": False,
                "message": "Authentication required for this test"
            }

        auth_headers = self.get_auth_headers()

        # Simulate an external API call
        return {
            "authenticated": True,
            "test_result": "success",
            "message": "Successfully tested authenticated request",
            "headers_sent": {k: "***" if "auth" in k.lower() or "token" in k.lower() else v
                           for k, v in auth_headers.items()},
            "auth_type": self.get_auth_context().auth_type.value
        }

    async def _get_auth_headers(self) -> Dict[str, Any]:
        """Get authentication headers (with sensitive data masked)."""
        auth_headers = self.get_auth_headers()

        # Mask sensitive information
        masked_headers = {}
        for key, value in auth_headers.items():
            if any(sensitive in key.lower() for sensitive in ["auth", "token", "key"]):
                masked_headers[key] = f"{value[:8]}..." if len(value) > 8 else "***"
            else:
                masked_headers[key] = value

        return {
            "headers": masked_headers,
            "count": len(auth_headers),
            "authenticated": self.is_authenticated()
        }


class BearerTokenValidationTool(AuthenticatedTool):
    """Tool that validates and displays bearer token information."""

    def __init__(self):
        super().__init__(
            name="bearer_token_validation_tool",
            description="Tool that validates and displays bearer token information for testing"
        )

    async def execute_with_context(self, validate_only: bool = False) -> Dict[str, Any]:
        """
        Validate and display bearer token information.

        Args:
            validate_only: If True, only validate without displaying details

        Returns:
            Dictionary with validation results
        """
        try:
            auth_context = self.get_auth_context()

            if not auth_context:
                return {
                    "valid": False,
                    "message": "No authentication context available",
                    "auth_required": True
                }

            if not auth_context.token:
                return {
                    "valid": False,
                    "message": "No token found in authentication context",
                    "auth_type": auth_context.auth_type.value
                }

            result = {
                "valid": True,
                "auth_type": auth_context.auth_type.value,
                "user_id": auth_context.user_id,
                "provider": auth_context.provider,
                "token_present": True
            }

            if not validate_only:
                # Add non-sensitive token info for debugging
                token = auth_context.token
                result.update({
                    "token_length": len(token),
                    "token_prefix": token[:8] if len(token) > 8 else "***",
                    "token_format": "Bearer" if auth_context.auth_type.value == "bearer_token" else auth_context.auth_type.value,
                    "metadata": auth_context.metadata
                })

            return result

        except Exception as e:
            logger.error(f"Bearer token validation failed: {e}")
            return {
                "valid": False,
                "error": str(e),
                "tool": self.name
            }


def create_authenticated_tools() -> list:
    """Create and return ADK FunctionTool instances for authenticated tools."""
    example_tool = ExampleAuthenticatedTool()
    validation_tool = BearerTokenValidationTool()

    return [
        FunctionTool(example_tool.execute_with_context),
        FunctionTool(validation_tool.execute_with_context)
    ]