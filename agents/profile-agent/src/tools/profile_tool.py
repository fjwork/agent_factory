"""
Profile Tool Implementation

This tool specifically handles user profile requests and information retrieval.
"""

import logging
from typing import Dict, Any, Optional, List
from google.adk.tools import ToolContext
from .authenticated_tool import AuthenticatedTool, AuthenticationError, ToolExecutionError

logger = logging.getLogger(__name__)


class ProfileTool(AuthenticatedTool):
    """Tool for retrieving and managing user profile information."""

    def __init__(self):
        super().__init__(
            name="profile_tool",
            description="Retrieves user profile information through OAuth authentication"
        )

    async def execute_authenticated(
        self,
        user_context: Dict[str, Any],
        request_type: str = "full_profile",
        specific_fields: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Retrieve user profile information.

        Args:
            user_context: User authentication context from OAuth
            request_type: Type of profile request (full_profile, basic_info, email_only)
            specific_fields: Specific profile fields to retrieve

        Returns:
            Formatted profile information
        """
        if not self.validate_user_context(user_context):
            raise AuthenticationError("Invalid user authentication context")

        self._log_tool_execution(
            user_context,
            "profile_request",
            {"request_type": request_type, "fields": specific_fields}
        )

        try:
            # Get real user information from OAuth provider API
            user_info = await self.fetch_real_user_info(user_context)
            user_id = self.get_user_id(user_context)
            provider = self.get_provider(user_context)

            # Format response based on request type
            if request_type == "full_profile":
                return self._format_full_profile(user_info, user_id, provider)
            elif request_type == "basic_info":
                return self._format_basic_info(user_info, user_id, provider)
            elif request_type == "email_only":
                return self._format_email_info(user_info, user_id, provider)
            elif request_type == "custom" and specific_fields:
                return self._format_custom_fields(user_info, user_id, provider, specific_fields)
            else:
                return self._format_full_profile(user_info, user_id, provider)

        except Exception as e:
            error_msg = f"Failed to retrieve profile information: {str(e)}"
            logger.error(error_msg)
            raise ToolExecutionError(error_msg)

    def _format_full_profile(self, user_info: Dict[str, Any], user_id: str, provider: str) -> Dict[str, Any]:
        """Format complete profile information."""
        return {
            "success": True,
            "profile_type": "full",
            "user_id": user_id,
            "provider": provider,
            "profile": {
                "name": user_info.get("name", "Not available"),
                "email": user_info.get("email", "Not available"),
                "given_name": user_info.get("given_name", "Not available"),
                "family_name": user_info.get("family_name", "Not available"),
                "picture": user_info.get("picture", "Not available"),
                "locale": user_info.get("locale", "Not available"),
                "verified_email": user_info.get("verified_email", False)
            },
            "summary": self._generate_profile_summary(user_info),
            "timestamp": self._get_timestamp()
        }

    def _format_basic_info(self, user_info: Dict[str, Any], user_id: str, provider: str) -> Dict[str, Any]:
        """Format basic profile information."""
        return {
            "success": True,
            "profile_type": "basic",
            "user_id": user_id,
            "provider": provider,
            "profile": {
                "name": user_info.get("name", "Not available"),
                "email": user_info.get("email", "Not available")
            },
            "summary": f"User: {user_info.get('name', 'Unknown')} ({user_info.get('email', 'No email')})",
            "timestamp": self._get_timestamp()
        }

    def _format_email_info(self, user_info: Dict[str, Any], user_id: str, provider: str) -> Dict[str, Any]:
        """Format email-only information."""
        return {
            "success": True,
            "profile_type": "email_only",
            "user_id": user_id,
            "provider": provider,
            "profile": {
                "email": user_info.get("email", "Not available"),
                "verified_email": user_info.get("verified_email", False)
            },
            "summary": f"Email: {user_info.get('email', 'Not available')}",
            "timestamp": self._get_timestamp()
        }

    def _format_custom_fields(
        self,
        user_info: Dict[str, Any],
        user_id: str,
        provider: str,
        fields: List[str]
    ) -> Dict[str, Any]:
        """Format specific requested fields."""
        custom_profile = {}
        for field in fields:
            if field in user_info:
                custom_profile[field] = user_info[field]
            else:
                custom_profile[field] = "Not available"

        return {
            "success": True,
            "profile_type": "custom",
            "user_id": user_id,
            "provider": provider,
            "requested_fields": fields,
            "profile": custom_profile,
            "summary": f"Custom profile data for {len(fields)} fields",
            "timestamp": self._get_timestamp()
        }

    def _generate_profile_summary(self, user_info: Dict[str, Any]) -> str:
        """Generate a human-readable profile summary."""
        name = user_info.get("name", "Unknown User")
        email = user_info.get("email", "No email provided")
        verified = user_info.get("verified_email", False)

        summary = f"Profile for {name}"
        if email != "No email provided":
            summary += f" with email {email}"
            if verified:
                summary += " (verified)"
            else:
                summary += " (unverified)"

        return summary

    async def execute_with_context(
        self,
        tool_context: ToolContext,
        request_type: str = "full_profile",
        specific_fields: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Execute profile tool using ADK ToolContext for user authentication.

        Args:
            tool_context: ADK ToolContext with session state
            request_type: Type of profile request (full_profile, basic_info, email_only)
            specific_fields: Specific profile fields to retrieve

        Returns:
            Formatted profile information
        """
        # Get user context from session state
        user_context = {
            "user_id": tool_context.state.get("oauth_user_id"),
            "provider": tool_context.state.get("oauth_provider"),
            "user_info": tool_context.state.get("oauth_user_info", {}),
            "token": tool_context.state.get("oauth_token")
        }

        # Validate that user is authenticated
        if not user_context["user_id"] or not user_context["token"]:
            return {
                "success": False,
                "error": "User authentication required. Please authenticate first.",
                "auth_required": True
            }

        # Call the existing authenticated method
        try:
            return await self.execute_authenticated(user_context, request_type, specific_fields)
        except AuthenticationError as e:
            return {
                "success": False,
                "error": f"Authentication failed: {str(e)}",
                "auth_required": True
            }
        except ToolExecutionError as e:
            return {
                "success": False,
                "error": f"Profile retrieval failed: {str(e)}"
            }


class ProfileSummaryTool(AuthenticatedTool):
    """Tool for generating profile summaries and insights."""

    def __init__(self):
        super().__init__(
            name="profile_summary_tool",
            description="Generates formatted summaries of user profile information"
        )

    async def execute_authenticated(
        self,
        user_context: Dict[str, Any],
        summary_style: str = "friendly"
    ) -> Dict[str, Any]:
        """
        Generate a profile summary.

        Args:
            user_context: User authentication context
            summary_style: Style of summary (friendly, formal, brief)

        Returns:
            Formatted profile summary
        """
        if not self.validate_user_context(user_context):
            raise AuthenticationError("Invalid user authentication context")

        self._log_tool_execution(
            user_context,
            "profile_summary",
            {"style": summary_style}
        )

        try:
            user_info = await self.fetch_real_user_info(user_context)
            user_id = self.get_user_id(user_context)
            provider = self.get_provider(user_context)

            if summary_style == "friendly":
                message = self._generate_friendly_summary(user_info)
            elif summary_style == "formal":
                message = self._generate_formal_summary(user_info)
            elif summary_style == "brief":
                message = self._generate_brief_summary(user_info)
            else:
                message = self._generate_friendly_summary(user_info)

            return {
                "success": True,
                "user_id": user_id,
                "provider": provider,
                "summary_style": summary_style,
                "message": message,
                "raw_profile": user_info,
                "timestamp": self._get_timestamp()
            }

        except Exception as e:
            error_msg = f"Failed to generate profile summary: {str(e)}"
            logger.error(error_msg)
            raise ToolExecutionError(error_msg)

    def _generate_friendly_summary(self, user_info: Dict[str, Any]) -> str:
        """Generate a friendly profile summary."""
        name = user_info.get("name", "there")
        email = user_info.get("email")

        summary = f"Hi {name}! "

        if email:
            summary += f"I can see you're logged in with the email {email}. "

        given_name = user_info.get("given_name")
        if given_name and given_name != name:
            summary += f"Your first name is {given_name}. "

        if user_info.get("verified_email"):
            summary += "Your email is verified, which is great for security! "

        return summary + "Is there anything specific about your profile you'd like to know?"

    def _generate_formal_summary(self, user_info: Dict[str, Any]) -> str:
        """Generate a formal profile summary."""
        name = user_info.get("name", "User")
        email = user_info.get("email", "No email provided")

        summary = f"Profile Information for {name}:\n"
        summary += f"- Email: {email}\n"

        if user_info.get("given_name"):
            summary += f"- First Name: {user_info['given_name']}\n"
        if user_info.get("family_name"):
            summary += f"- Last Name: {user_info['family_name']}\n"
        if user_info.get("locale"):
            summary += f"- Locale: {user_info['locale']}\n"

        summary += f"- Email Verified: {user_info.get('verified_email', False)}"

        return summary

    def _generate_brief_summary(self, user_info: Dict[str, Any]) -> str:
        """Generate a brief profile summary."""
        name = user_info.get("name", "Unknown")
        email = user_info.get("email", "No email")
        return f"{name} ({email})"

    async def execute_with_context(
        self,
        tool_context: ToolContext,
        summary_style: str = "friendly"
    ) -> Dict[str, Any]:
        """
        Execute profile summary tool using ADK ToolContext for user authentication.

        Args:
            tool_context: ADK ToolContext with session state
            summary_style: Style of summary (friendly, formal, brief)

        Returns:
            Formatted profile summary
        """
        # Get user context from session state
        user_context = {
            "user_id": tool_context.state.get("oauth_user_id"),
            "provider": tool_context.state.get("oauth_provider"),
            "user_info": tool_context.state.get("oauth_user_info", {}),
            "token": tool_context.state.get("oauth_token")
        }

        # Validate that user is authenticated
        if not user_context["user_id"] or not user_context["token"]:
            return {
                "success": False,
                "error": "User authentication required. Please authenticate first.",
                "auth_required": True
            }

        # Call the existing authenticated method
        try:
            return await self.execute_authenticated(user_context, summary_style)
        except AuthenticationError as e:
            return {
                "success": False,
                "error": f"Authentication failed: {str(e)}",
                "auth_required": True
            }
        except ToolExecutionError as e:
            return {
                "success": False,
                "error": f"Profile summary generation failed: {str(e)}"
            }