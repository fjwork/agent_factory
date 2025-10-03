"""
MCP Toolkit Integration

This module provides authenticated MCP toolset integration based on your sample code.
It includes token management, caching, and authentication header injection.
"""

import base64
import json
import logging
import os
import time
from typing import Dict, List, Optional, Any

import jwt
import google.auth.transport.requests
import google.oauth2.id_token
from google.auth import exceptions as google_auth_exceptions
from google.adk.tools.base_tool import BaseTool
from google.adk.tools.mcp_tool.mcp_session_manager import retry_on_closed_resource
from google.adk.tools.mcp_tool.mcp_toolset import (
    MCPToolset,
    StreamableHTTPConnectionParams,
)
from google.adk.agents.readonly_context import ReadonlyContext

logger = logging.getLogger(__name__)

# Global cache for toolsets (similar to your sample code)
toolset_cache: Dict[str, Dict[str, Any]] = {}


def decode_jwt_no_verify(token: str) -> dict:
    """
    Decode a JWT token's payload without verifying signature.

    This helper is intentionally lightweight and only used for reading
    untrusted tokens where signature verification is not required.
    """
    try:
        parts = token.split(".")
        if len(parts) < 2:
            raise ValueError("Invalid JWT token format")
        payload_b64 = parts[1]
        # Pad base64 if necessary
        padding = "=" * (-len(payload_b64) % 4)
        payload_b64 += padding
        decoded = base64.urlsafe_b64decode(payload_b64)
        return json.loads(decoded)
    except Exception as e:
        raise ValueError(f"Failed to decode JWT payload: {e}") from e


class MCPToolsetWithAuth(MCPToolset):
    """
    Enhanced MCPToolset with authentication and caching capabilities.

    Features:
    - Automatic JWT token management with expiration checking
    - Tool caching for performance optimization
    - Configurable authentication headers
    - Token refresh based on configurable thresholds
    """

    def __init__(
        self,
        name: str,
        url: str,
        timeout: int = 60,
        auth_required: bool = True,
        auth_header: str = "X-Serverless-Authorization",
        token_refresh_threshold_mins: int = 15,
        headers: Optional[Dict[str, str]] = None
    ):
        """
        Initialize MCP toolset with authentication.

        Args:
            name: Unique name for this toolset
            url: MCP server URL
            timeout: Request timeout in seconds
            auth_required: Whether authentication is required
            auth_header: Header name for authentication token
            token_refresh_threshold_mins: Minutes before expiry to refresh token
            headers: Additional static headers
        """
        # Create connection parameters
        connection_params = StreamableHTTPConnectionParams(
            url=url + ("/mcp" if not url.endswith("/mcp") else ""),
            timeout=timeout,
            headers=headers or {}
        )

        # Initialize parent class
        super().__init__(connection_params=connection_params)

        # Store authentication configuration
        self._tool_set_name = name
        self.auth_required = auth_required
        self.auth_header = auth_header
        self.token_refresh_threshold_mins = token_refresh_threshold_mins
        self.base_url = url

        # Initialize cache entry for this toolset
        if self._tool_set_name not in toolset_cache:
            toolset_cache[self._tool_set_name] = {}

        logger.info(f"Initialized MCP toolset '{name}' for URL: {url}")

    @retry_on_closed_resource
    async def get_tools(self, readonly_context: Optional[ReadonlyContext] = None) -> List[BaseTool]:
        """
        Get tools with caching support.

        This method caches tools after first retrieval to improve performance,
        similar to your sample code pattern.
        """
        # Check if tools are already cached
        if "tools" in toolset_cache[self._tool_set_name]:
            logger.debug(f"Found cached tools for toolset {self._tool_set_name}")
            return toolset_cache[self._tool_set_name]["tools"]

        # Fetch tools from parent class
        logger.info(f"Fetching tools for toolset {self._tool_set_name}")
        original_tools = await super().get_tools(readonly_context)

        # Cache the tools
        toolset_cache[self._tool_set_name]["tools"] = original_tools
        logger.info(f"Cached {len(original_tools)} tools for {self._tool_set_name}")

        return original_tools

    def get_auth_token_callback(self):
        """
        Return a callback function for auth token management.

        This creates a callback that can be used with the ADK agent's
        before_agent_callback parameter.
        """
        def auth_callback(callback_context):
            return self._inject_auth_token(callback_context)

        return auth_callback

    def _inject_auth_token(self, callback_context) -> None:
        """
        Inject authentication token into MCP connection headers.

        This method follows the pattern from your sample code for token management.
        """
        if not self.auth_required:
            logger.debug(f"Authentication not required for {self._tool_set_name}")
            return None

        try:
            cache_entry = toolset_cache[self._tool_set_name]

            # Check if token was never added or needs refresh
            if not self._has_valid_token(cache_entry):
                logger.info(f"Getting new token for {self._tool_set_name}")
                self._refresh_token(cache_entry)
            else:
                logger.debug(f"Using cached valid token for {self._tool_set_name}")
                self._apply_cached_token(cache_entry)

        except Exception as e:
            logger.error(f"Failed to inject auth token for {self._tool_set_name}: {e}")

        return None

    def _has_valid_token(self, cache_entry: Dict[str, Any]) -> bool:
        """Check if we have a valid, non-expired token."""
        if "token_expiration_time" not in cache_entry:
            return False

        # Check if token will expire within threshold
        time_after_threshold = (
            int(time.time()) + self.token_refresh_threshold_mins * 60
        )

        expiration_time = cache_entry["token_expiration_time"]
        is_valid = time_after_threshold < expiration_time

        logger.debug(
            f"Token expires at {expiration_time}, "
            f"threshold time: {time_after_threshold}, "
            f"valid: {is_valid}"
        )

        return is_valid

    def _refresh_token(self, cache_entry: Dict[str, Any]):
        """Refresh authentication token."""
        try:
            # Get new ID token
            id_token = self._get_id_token(self.base_url)

            # Decode token to get expiration
            try:
                if hasattr(jwt, "decode"):
                    decoded_payload = jwt.decode(id_token, options={"verify_signature": False})
                else:
                    decoded_payload = decode_jwt_no_verify(id_token)
            except Exception:
                decoded_payload = decode_jwt_no_verify(id_token)

            # Update connection headers
            self._connection_params.headers = self._connection_params.headers or {}
            bearer_token = f"Bearer {id_token}"
            self._connection_params.headers[self.auth_header] = bearer_token

            # Update cache
            cache_entry["prev_used_token"] = bearer_token
            cache_entry["token_expiration_time"] = decoded_payload["exp"]

            logger.info(f"Successfully refreshed token for {self._tool_set_name}")
            logger.debug(f"Token expires at: {decoded_payload['exp']}")

        except Exception as e:
            logger.error(f"Failed to refresh token for {self._tool_set_name}: {e}")
            raise

    def _apply_cached_token(self, cache_entry: Dict[str, Any]):
        """Apply cached token to connection headers."""
        cached_token = cache_entry.get("prev_used_token")
        if cached_token:
            self._connection_params.headers = self._connection_params.headers or {}
            self._connection_params.headers[self.auth_header] = cached_token
            logger.debug(f"Applied cached token for {self._tool_set_name}")

    def _get_id_token(self, audience: str) -> str:
        """
        Get ID token for authentication.

        This method gets an ID token from Google Cloud credentials
        for authenticating with the MCP server.
        """
        try:
            auth_req = google.auth.transport.requests.Request()
            id_token = google.oauth2.id_token.fetch_id_token(auth_req, audience)
            logger.debug(f"Successfully obtained ID token for audience: {audience}")
            return id_token
        except google_auth_exceptions.DefaultCredentialsError as e:
            logger.error(f"Failed to get default credentials: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to fetch ID token: {e}")
            raise

    def get_cache_status(self) -> Dict[str, Any]:
        """Get cache status for this toolset."""
        cache_entry = toolset_cache.get(self._tool_set_name, {})
        return {
            "toolset_name": self._tool_set_name,
            "has_cached_tools": "tools" in cache_entry,
            "tools_count": len(cache_entry.get("tools", [])),
            "has_token": "prev_used_token" in cache_entry,
            "token_expiration": cache_entry.get("token_expiration_time"),
            "current_time": int(time.time()),
            "token_valid": self._has_valid_token(cache_entry) if "token_expiration_time" in cache_entry else False
        }

    def clear_cache(self):
        """Clear cache for this toolset."""
        if self._tool_set_name in toolset_cache:
            toolset_cache[self._tool_set_name].clear()
            logger.info(f"Cleared cache for toolset {self._tool_set_name}")

    @classmethod
    def clear_all_caches(cls):
        """Clear all toolset caches."""
        global toolset_cache
        toolset_cache.clear()
        logger.info("Cleared all toolset caches")

    @classmethod
    def get_global_cache_status(cls) -> Dict[str, Any]:
        """Get status of global toolset cache."""
        return {
            "total_toolsets": len(toolset_cache),
            "toolsets": {
                name: {
                    "has_tools": "tools" in cache_data,
                    "tools_count": len(cache_data.get("tools", [])),
                    "has_token": "prev_used_token" in cache_data,
                    "token_expiration": cache_data.get("token_expiration_time")
                }
                for name, cache_data in toolset_cache.items()
            }
        }


def create_mcp_auth_callback(toolsets: List[MCPToolsetWithAuth]):
    """
    Create a unified auth callback for multiple MCP toolsets.

    This is useful when you have multiple MCP toolsets that all need
    authentication token injection.

    Args:
        toolsets: List of MCP toolsets that need authentication

    Returns:
        Callback function for use with ADK agent
    """
    def unified_auth_callback(callback_context):
        """Unified callback that updates all toolsets."""
        for toolset in toolsets:
            try:
                toolset._inject_auth_token(callback_context)
            except Exception as e:
                logger.error(f"Failed to inject auth for {toolset._tool_set_name}: {e}")

        return None

    return unified_auth_callback


def create_weather_mcp_toolset(
    name: str = "weather_toolset",
    url: Optional[str] = None
) -> MCPToolsetWithAuth:
    """
    Create a weather MCP toolset based on your sample code.

    This is a convenience function that creates a properly configured
    weather MCP toolset similar to your example.

    Args:
        name: Name for the toolset
        url: MCP server URL (defaults to MCP_SERVER_URL env var)

    Returns:
        Configured MCPToolsetWithAuth instance
    """
    server_url = url or os.getenv("MCP_SERVER_URL", "http://localhost:8080")

    return MCPToolsetWithAuth(
        name=name,
        url=server_url,
        timeout=60,
        auth_required=True,
        auth_header="X-Serverless-Authorization",
        token_refresh_threshold_mins=int(os.getenv("TOKEN_REFRESH_THRESHOLD_MINS", "15"))
    )