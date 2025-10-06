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
        # Create connection parameters with robust type handling
        logger.debug(f"URL type: {type(url)}, URL value: {url}")

        # Ensure URL is always a string
        if not isinstance(url, str):
            url = str(url)
            logger.debug(f"Converted URL to string: {url}")

        try:
            final_url = url + ("/mcp" if not url.endswith("/mcp") else "")
            logger.debug(f"Final URL: {final_url}")
        except TypeError as e:
            logger.error(f"URL concatenation error: {e}, url={url}, type={type(url)}")
            raise

        # Prepare headers including bearer token at initialization time
        initial_headers = headers or {}

        # Store name first so we can use it in bearer token retrieval
        self._tool_set_name = name

        # Attempt to get bearer token during initialization (if available)
        bearer_token = self._get_bearer_token_at_init(name)
        if bearer_token:
            initial_headers["X-Original-Bearer-Token"] = bearer_token
            logger.info(f"🎯 Set bearer token in connection headers during init for {name}: {bearer_token}")
        else:
            logger.debug(f"🔍 No bearer token available during initialization for {name} (will be injected dynamically during auth callbacks)")

        connection_params = StreamableHTTPConnectionParams(
            url=final_url,
            timeout=timeout,
            headers=initial_headers
        )

        # Store authentication configuration BEFORE parent init
        # (tool_set_name already set above for bearer token retrieval)
        self.auth_required = auth_required
        self.auth_header = auth_header
        self.token_refresh_threshold_mins = token_refresh_threshold_mins
        self.base_url = url

        # Initialize parent class
        super().__init__(connection_params=connection_params)

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
        Now supports dual headers: JWT (primary) + original bearer token (passthrough).
        """
        logger.info(f"🚀 MCP auth callback invoked for {self._tool_set_name}")

        if not self.auth_required:
            logger.debug(f"Authentication not required for {self._tool_set_name}")
            return None

        try:
            cache_entry = toolset_cache[self._tool_set_name]

            # Handle JWT token (primary authentication)
            if not self._has_valid_token(cache_entry):
                logger.info(f"Getting new JWT token for {self._tool_set_name}")
                self._refresh_token(cache_entry)
            else:
                logger.debug(f"Using cached JWT token for {self._tool_set_name}")
                self._apply_cached_token(cache_entry)

            # Handle bearer token passthrough (secondary authentication)
            logger.info(f"🔄 Starting bearer token passthrough for {self._tool_set_name}")
            self._inject_bearer_token()

            # Log comprehensive auth status for debugging
            logger.info(f"🔍 Logging comprehensive auth status for {self._tool_set_name}")
            self.log_auth_debug_info()

            logger.info(f"✅ Dual auth injection completed for {self._tool_set_name}")

        except Exception as e:
            logger.error(f"Failed to inject auth token for {self._tool_set_name}: {e}")

        return None

    def _inject_bearer_token(self) -> None:
        """
        Inject bearer token into MCP connection headers during auth callback.

        This method retrieves the bearer token from the global registry and
        dynamically updates the connection headers with X-Original-Bearer-Token.
        """
        logger.debug(f"🔍 Starting bearer token injection for {self._tool_set_name}")

        try:
            # Retrieve bearer token from global registry
            logger.debug(f"🔄 Attempting to retrieve bearer token from global registry for {self._tool_set_name}")
            bearer_token = self._get_bearer_token_from_registry()

            if bearer_token:
                logger.info(f"✅ Retrieved bearer token for {self._tool_set_name}: {bearer_token}")

                # Ensure connection headers exist
                if not self._connection_params.headers:
                    logger.debug(f"🔧 Creating new headers dict for {self._tool_set_name}")
                    self._connection_params.headers = {}
                else:
                    logger.debug(f"🔧 Using existing headers dict for {self._tool_set_name} (current count: {len(self._connection_params.headers)})")

                # Inject bearer token header
                self._connection_params.headers["X-Original-Bearer-Token"] = bearer_token
                logger.info(f"✅ Injected bearer token into connection headers for {self._tool_set_name}")

                # Log current headers for debugging (sanitized)
                headers_summary = {}
                for k, v in self._connection_params.headers.items():
                    if k in ["X-Serverless-Authorization", "X-Original-Bearer-Token"]:
                        if v and len(v) > 10:
                            headers_summary[k] = f"{v[:6]}...{v[-4:]}"
                        else:
                            headers_summary[k] = v
                    else:
                        headers_summary[k] = v
                logger.info(f"🔍 Current auth headers for {self._tool_set_name}: {headers_summary}")
            else:
                logger.warning(f"❌ No bearer token available for injection in {self._tool_set_name}")

        except Exception as e:
            logger.error(f"💥 Failed to inject bearer token for {self._tool_set_name}: {e}")
            import traceback
            logger.error(f"💥 Stack trace: {traceback.format_exc()}")

    def _get_bearer_token_from_registry(self) -> Optional[str]:
        """
        Get bearer token from global auth registry with improved error handling.

        Returns:
            Bearer token string if available, None otherwise
        """
        logger.debug(f"🔍 Entering _get_bearer_token_from_registry for {self._tool_set_name}")

        try:
            # Import the handler class to access its global registry
            logger.debug(f"🔄 Importing AuthenticatedRequestHandler for {self._tool_set_name}")
            from agent_a2a.handlers import AuthenticatedRequestHandler

            # Check if the registry exists and has any entries
            if not hasattr(AuthenticatedRequestHandler, '_oauth_registry'):
                logger.warning(f"❌ No _oauth_registry attribute found on AuthenticatedRequestHandler for {self._tool_set_name}")
                return None

            registry = AuthenticatedRequestHandler._oauth_registry
            logger.debug(f"🔍 Registry type: {type(registry)}, registry: {registry}")

            if not registry:
                logger.warning(f"❌ Global auth registry is empty for {self._tool_set_name}")
                return None

            logger.info(f"✅ Found global registry with {len(registry)} entries for {self._tool_set_name}")

            # Get the most recent auth context (assuming latest is most relevant)
            user_id, oauth_context = next(iter(registry.items()))
            logger.info(f"🔍 Checking auth context for user: {user_id}")
            logger.debug(f"🔍 OAuth context keys: {list(oauth_context.keys())}")
            logger.debug(f"🔍 OAuth context: {oauth_context}")

            # Extract bearer token
            bearer_token = oauth_context.get('oauth_token')
            if bearer_token:
                logger.info(f"✅ Retrieved bearer token for user {user_id} in {self._tool_set_name}: {bearer_token}")
                return bearer_token
            else:
                logger.warning(f"❌ No oauth_token found in auth context for {user_id}")
                logger.debug(f"❌ Available keys in context: {list(oauth_context.keys())}")
                return None

        except Exception as e:
            logger.error(f"💥 Failed to get bearer token from registry for {self._tool_set_name}: {e}")
            import traceback
            logger.error(f"💥 Stack trace: {traceback.format_exc()}")
            return None

    def _get_bearer_token_at_init(self, toolset_name: str) -> Optional[str]:
        """
        Get bearer token from global auth registry during toolset initialization.

        This method is called during initialization but typically returns None
        since bearer tokens are stored only after authenticated requests arrive.
        Left for potential future use or when tokens are pre-populated.

        Args:
            toolset_name: Name of the toolset for logging purposes
        """
        # Delegate to the main bearer token retrieval method
        token = self._get_bearer_token_from_registry()
        if token:
            logger.info(f"✅ Found bearer token during init for {toolset_name}: {token}")
        else:
            logger.debug(f"ℹ️ No bearer token available during init for {toolset_name} (expected - tokens come after auth)")
        return token



    def _has_valid_token(self, cache_entry: Dict[str, Any]) -> bool:
        """Check if we have a valid, non-expired token."""
        if "token_expiration_time" not in cache_entry:
            return False

        try:
            # Ensure all values are integers for proper calculation
            current_time = int(time.time())
            threshold_mins = int(self.token_refresh_threshold_mins)
            expiration_time = int(cache_entry["token_expiration_time"])

            # Check if token will expire within threshold
            time_after_threshold = current_time + (threshold_mins * 60)

            is_valid = time_after_threshold < expiration_time

            logger.debug(
                f"Token expires at {expiration_time}, "
                f"current time: {current_time}, "
                f"threshold time: {time_after_threshold}, "
                f"valid: {is_valid}"
            )

            return is_valid

        except (ValueError, TypeError) as e:
            logger.error(f"Error in token expiration calculation for {self._tool_set_name}: {e}")
            # If we can't calculate expiration, assume token is invalid
            return False

    def _refresh_token(self, cache_entry: Dict[str, Any]):
        """Refresh JWT authentication token."""
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

            # Ensure headers dict exists
            if not self._connection_params.headers:
                self._connection_params.headers = {}

            # Update connection headers with JWT token
            bearer_token = f"Bearer {id_token}"
            self._connection_params.headers[self.auth_header] = bearer_token

            # Update cache
            cache_entry["prev_used_token"] = bearer_token
            cache_entry["token_expiration_time"] = decoded_payload["exp"]

            logger.info(f"Successfully refreshed JWT token for {self._tool_set_name}")
            logger.debug(f"JWT token expires at: {decoded_payload['exp']}")

        except Exception as e:
            logger.error(f"Failed to refresh JWT token for {self._tool_set_name}: {e}")
            raise

    def _apply_cached_token(self, cache_entry: Dict[str, Any]):
        """Apply cached JWT token to connection headers."""
        cached_token = cache_entry.get("prev_used_token")
        if cached_token:
            # Ensure headers dict exists
            if not self._connection_params.headers:
                self._connection_params.headers = {}

            # Apply JWT token
            self._connection_params.headers[self.auth_header] = cached_token
            logger.debug(f"Applied cached JWT token for {self._tool_set_name}")
        else:
            logger.warning(f"No cached JWT token found for {self._tool_set_name}")

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

    def get_auth_status(self) -> Dict[str, Any]:
        """
        Get comprehensive authentication status for debugging.

        Returns:
            Dictionary containing JWT and bearer token status
        """
        try:
            # JWT token status
            cache_entry = toolset_cache.get(self._tool_set_name, {})
            jwt_status = {
                "has_jwt_token": "prev_used_token" in cache_entry,
                "jwt_expiration": cache_entry.get("token_expiration_time"),
                "jwt_valid": self._has_valid_token(cache_entry) if "token_expiration_time" in cache_entry else False
            }

            # Bearer token status
            bearer_token = self._get_bearer_token_from_registry()
            bearer_status = {
                "bearer_token_available": bearer_token is not None,
                "bearer_token_value": bearer_token if bearer_token else None
            }

            # Connection headers status
            headers_status = {
                "has_connection_headers": self._connection_params.headers is not None,
                "jwt_header_present": False,
                "bearer_header_present": False
            }

            if self._connection_params.headers:
                headers_status["jwt_header_present"] = self.auth_header in self._connection_params.headers
                headers_status["bearer_header_present"] = "X-Original-Bearer-Token" in self._connection_params.headers
                headers_status["header_count"] = len(self._connection_params.headers)

            return {
                "toolset_name": self._tool_set_name,
                "jwt_status": jwt_status,
                "bearer_status": bearer_status,
                "headers_status": headers_status,
                "timestamp": int(time.time())
            }

        except Exception as e:
            logger.error(f"Failed to get auth status for {self._tool_set_name}: {e}")
            return {
                "toolset_name": self._tool_set_name,
                "error": str(e),
                "timestamp": int(time.time())
            }

    def log_auth_debug_info(self) -> None:
        """Log comprehensive authentication debug information."""
        try:
            auth_status = self.get_auth_status()
            logger.info(f"🔍 Auth Debug Info for {self._tool_set_name}:")
            logger.info(f"   JWT Status: {auth_status['jwt_status']}")
            logger.info(f"   Bearer Status: {auth_status['bearer_status']}")
            logger.info(f"   Headers Status: {auth_status['headers_status']}")

            # Log actual headers (sanitized)
            if self._connection_params.headers:
                sanitized_headers = {}
                for key, value in self._connection_params.headers.items():
                    if key in ["X-Serverless-Authorization", "X-Original-Bearer-Token"]:
                        # Show only first/last few characters for security
                        if value and len(value) > 10:
                            sanitized_headers[key] = f"{value[:6]}...{value[-4:]}"
                        else:
                            sanitized_headers[key] = value
                    else:
                        sanitized_headers[key] = value
                logger.info(f"   Actual Headers: {sanitized_headers}")

        except Exception as e:
            logger.error(f"Failed to log auth debug info for {self._tool_set_name}: {e}")

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
    # Ensure server_url is always a string
    if not isinstance(server_url, str):
        server_url = str(server_url)

    # Ensure token refresh threshold is properly converted to int
    try:
        token_refresh_mins = int(os.getenv("TOKEN_REFRESH_THRESHOLD_MINS", "15"))
    except (ValueError, TypeError) as e:
        logger.warning(f"Invalid TOKEN_REFRESH_THRESHOLD_MINS value, using default 15: {e}")
        token_refresh_mins = 15

    return MCPToolsetWithAuth(
        name=name,
        url=server_url,
        timeout=60,
        auth_required=True,
        auth_header="X-Serverless-Authorization",
        token_refresh_threshold_mins=token_refresh_mins
    )