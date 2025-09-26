"""
Authentication Verification Tool

This tool verifies that authentication context is properly received and displays details.
"""

import logging
from datetime import datetime
from typing import Dict, Any, Optional
from google.adk.tools import ToolContext

# Import from agent-template
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "agent-template", "src"))

from tools.authenticated_tool import AuthenticatedTool, AuthenticationError

logger = logging.getLogger(__name__)


class AuthVerificationTool(AuthenticatedTool):
    """Tool for verifying authentication context is properly received."""

    def __init__(self):
        super().__init__(
            name="auth_verification_tool",
            description="Verifies authentication context and displays auth details for testing"
        )

    async def execute_authenticated(
        self,
        user_context: Dict[str, Any],
        test_message: str = "Testing authentication flow",
        **kwargs
    ) -> Dict[str, Any]:
        """
        Verify and display authentication context details.

        Args:
            user_context: User authentication context from OAuth/Bearer token
            test_message: Custom message for the test
            **kwargs: Additional parameters

        Returns:
            Dictionary containing authentication verification results
        """
        if not self.validate_user_context(user_context):
            raise AuthenticationError("Invalid user authentication context")

        self._log_tool_execution(
            user_context,
            "auth_verification",
            {"test_message": test_message}
        )

        try:
            # Extract all available auth information
            user_id = self.get_user_id(user_context)
            provider = self.get_provider(user_context)
            user_info = self.get_user_info(user_context)
            access_token = self.get_access_token(user_context)

            # Get additional auth context details
            auth_type = user_context.get("auth_type", "unknown")
            authenticated = user_context.get("authenticated", False)

            # Create detailed auth report
            auth_details = {
                "user_id": user_id,
                "provider": provider,
                "auth_type": auth_type,
                "authenticated": authenticated,
                "token_present": bool(access_token),
                "token_length": len(access_token) if access_token else 0,
                "user_info_keys": list(user_info.keys()) if user_info else [],
                "context_keys": list(user_context.keys()),
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }

            # If we have user info, include some safe details
            if user_info:
                safe_user_info = {
                    "name": user_info.get("name", "N/A"),
                    "email": user_info.get("email", "N/A"),
                    "has_picture": bool(user_info.get("picture"))
                }
                auth_details["user_info"] = safe_user_info

            logger.info(f"✅ Authentication verification successful for user: {user_id}")
            logger.info(f"Auth details: {auth_details}")

            return {
                "success": True,
                "message": f"✅ Authentication received successfully! {test_message}",
                "tool_name": self.name,
                "auth_details": auth_details,
                "verification_status": "PASSED",
                "test_timestamp": datetime.utcnow().isoformat() + "Z"
            }

        except Exception as e:
            error_msg = f"Authentication verification failed: {str(e)}"
            logger.error(error_msg)
            return {
                "success": False,
                "message": f"❌ Authentication verification failed: {str(e)}",
                "tool_name": self.name,
                "verification_status": "FAILED",
                "error": error_msg,
                "test_timestamp": datetime.utcnow().isoformat() + "Z"
            }

    async def execute_with_context(
        self,
        context: ToolContext,
        test_message: str = "Testing authentication flow",
        **kwargs
    ) -> Dict[str, Any]:
        """
        Execute the tool with ADK ToolContext.

        This method extracts user context from the ADK session state and calls execute_authenticated.
        """
        try:
            # Extract user context from ADK session
            user_context = None
            if hasattr(context, 'session') and context.session:
                # Try to get user context from session state
                if hasattr(context.session, 'state') and context.session.state:
                    user_context = context.session.state.get('user_context')

                # Also check session metadata
                if not user_context and hasattr(context.session, 'metadata'):
                    user_context = context.session.metadata.get('user_context')

            if not user_context:
                return {
                    "success": False,
                    "message": "❌ No user authentication context found in session",
                    "tool_name": self.name,
                    "verification_status": "FAILED",
                    "error": "User context not found in ADK session",
                    "test_timestamp": datetime.utcnow().isoformat() + "Z"
                }

            # Call the authenticated execution method
            return await self.execute_authenticated(user_context, test_message, **kwargs)

        except Exception as e:
            error_msg = f"Tool execution failed: {str(e)}"
            logger.error(error_msg)
            return {
                "success": False,
                "message": f"❌ Tool execution error: {str(e)}",
                "tool_name": self.name,
                "verification_status": "ERROR",
                "error": error_msg,
                "test_timestamp": datetime.utcnow().isoformat() + "Z"
            }