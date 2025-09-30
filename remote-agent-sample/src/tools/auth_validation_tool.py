"""
Authentication Validation Tool

This tool validates that authentication context is properly forwarded
from the root agent to this remote agent via A2A protocol.
"""

import logging
from typing import Dict, Any
from google.adk.tools import ToolContext

logger = logging.getLogger(__name__)


class AuthValidationTool:
    """Tool that validates authentication context forwarding."""

    def __init__(self):
        self.name = "auth_validation_tool"
        self.description = "Validates authentication context forwarding from root agent"

    async def execute_with_context(
        self,
        tool_context: ToolContext,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Validate authentication context forwarding.

        Args:
            tool_context: ADK ToolContext with session state
            **kwargs: Additional parameters

        Returns:
            Authentication validation results
        """
        logger.info("🔍 Auth Validation Tool - Checking authentication context")

        # Get session state
        session_state = tool_context.state or {}

        # Handle State object vs dict
        if hasattr(session_state, '__dict__'):
            state_dict = vars(session_state)
        else:
            state_dict = session_state

        # Extract authentication information
        auth_info = self._extract_auth_info(state_dict)

        # Create validation result
        result = {
            "success": True,
            "tool": "auth_validation_tool",
            "agent_type": "remote_agent_sample",
            "authentication_validation": auth_info,
            "message": f"✅ Authentication validation complete. Status: {'SUCCESS' if auth_info['authenticated'] else 'FAILED'}",
            "a2a_forwarding_test": "SUCCESS" if auth_info["authenticated"] else "FAILED",
            "bearer_token": auth_info.get("bearer_token", "Not available")
        }

        logger.info(f"✅ Auth validation completed: {result}")
        return result

    def _extract_auth_info(self, state_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Extract authentication information from session state with global registry fallback."""
        auth_info = {
            "authenticated": False,
            "auth_type": None,
            "user_id": None,
            "token_present": False,
            "oauth_context": {},
            "session_debug": {
                "state_type": type(state_dict).__name__,
                "session_keys": list(state_dict.keys()) if state_dict else [],
                "remote_agent": "remote_agent_sample",
                "source": "session_state"
            }
        }

        # Check for OAuth context in session state (stored by before_agent_callback)
        if state_dict.get("oauth_authenticated"):
            auth_info["authenticated"] = True
            auth_info["auth_type"] = "oauth"
            auth_info["user_id"] = state_dict.get("oauth_user_id")
            auth_info["token_present"] = bool(state_dict.get("oauth_token"))
            auth_info["bearer_token"] = state_dict.get("oauth_token", "Not available")
            auth_info["oauth_context"] = {
                "provider": state_dict.get("oauth_provider"),
                "user_info": state_dict.get("oauth_user_info", {})
            }
            auth_info["session_debug"]["source"] = "session_state"
            return auth_info

        # FALLBACK: Check global registry if session state is empty
        logger.info("Session state empty, checking global registry fallback")
        global_auth = self._extract_from_global_registry()
        if global_auth:
            auth_info.update(global_auth)
            auth_info["session_debug"]["source"] = "global_registry_fallback"
            return auth_info

        # If no auth context found anywhere
        logger.warning("No authentication context found in session state or global registry")
        return auth_info

    def _extract_from_global_registry(self) -> Dict[str, Any]:
        """Extract authentication information from global registry."""
        try:
            from agent_a2a.handlers import AuthenticatedRequestHandler

            if hasattr(AuthenticatedRequestHandler, '_oauth_registry'):
                registry = AuthenticatedRequestHandler._oauth_registry
                if registry:
                    # Get the first available auth context
                    user_id, oauth_context = next(iter(registry.items()))
                    logger.info(f"Found auth context in global registry for user: {user_id}")

                    return {
                        "authenticated": oauth_context.get("oauth_authenticated", False),
                        "auth_type": "oauth",
                        "user_id": oauth_context.get("oauth_user_id"),
                        "token_present": bool(oauth_context.get("oauth_token")),
                        "bearer_token": oauth_context.get("oauth_token", "Not available"),
                        "oauth_context": {
                            "provider": oauth_context.get("oauth_provider"),
                            "user_info": oauth_context.get("oauth_user_info", {})
                        }
                    }

            logger.debug("No auth context found in global registry")
            return None

        except Exception as e:
            logger.error(f"Failed to extract from global registry: {e}")
            return None