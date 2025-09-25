"""
Profile Example Tool

This tool demonstrates how to retrieve and format user profile information
using OAuth authentication. It serves as a template for building profile-related tools.
"""

import logging
from typing import Dict, Any, Optional, List
from tools.authenticated_tool import AuthenticatedTool, AuthenticationError, ToolExecutionError

logger = logging.getLogger(__name__)


class ProfileExampleTool(AuthenticatedTool):
    """Example tool for retrieving and managing user profile information."""

    def __init__(self):
        super().__init__(
            name="profile_example_tool",
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
            "timestamp": self._get_timestamp()
        }

    def _format_email_info(self, user_info: Dict[str, Any], user_id: str, provider: str) -> Dict[str, Any]:
        """Format email-only profile information."""
        return {
            "success": True,
            "profile_type": "email_only",
            "user_id": user_id,
            "provider": provider,
            "profile": {
                "email": user_info.get("email", "Not available"),
                "verified_email": user_info.get("verified_email", False)
            },
            "timestamp": self._get_timestamp()
        }

    def _format_custom_fields(self, user_info: Dict[str, Any], user_id: str, provider: str, fields: List[str]) -> Dict[str, Any]:
        """Format custom selected fields."""
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
            "profile": custom_profile,
            "requested_fields": fields,
            "timestamp": self._get_timestamp()
        }

    def _generate_profile_summary(self, user_info: Dict[str, Any]) -> str:
        """Generate a human-readable profile summary."""
        name = user_info.get("name", "User")
        email = user_info.get("email", "No email")

        summary = f"Profile for {name}"
        if email != "No email":
            summary += f" ({email})"
            if user_info.get("verified_email"):
                summary += " (verified)"
            else:
                summary += " (unverified)"

        return summary


class ProfileSummaryExampleTool(AuthenticatedTool):
    """Example tool for generating formatted profile summaries."""

    def __init__(self):
        super().__init__(
            name="profile_summary_example_tool",
            description="Generates formatted summaries of user profile information"
        )

    async def execute_authenticated(
        self,
        user_context: Dict[str, Any],
        summary_style: str = "friendly"
    ) -> Dict[str, Any]:
        """
        Generate a formatted profile summary.

        Args:
            user_context: User authentication context from OAuth
            summary_style: Style of summary (friendly, formal, brief)

        Returns:
            Formatted profile summary
        """
        if not self.validate_user_context(user_context):
            raise AuthenticationError("Invalid user authentication context")

        self._log_tool_execution(
            user_context,
            "profile_summary",
            {"summary_style": summary_style}
        )

        try:
            # Get real user information from OAuth provider API
            user_info = await self.fetch_real_user_info(user_context)
            user_id = self.get_user_id(user_context)
            provider = self.get_provider(user_context)

            # Generate summary based on style
            if summary_style == "friendly":
                summary = self._generate_friendly_summary(user_info)
            elif summary_style == "formal":
                summary = self._generate_formal_summary(user_info)
            elif summary_style == "brief":
                summary = self._generate_brief_summary(user_info)
            else:
                summary = self._generate_friendly_summary(user_info)

            return {
                "success": True,
                "user_id": user_id,
                "provider": provider,
                "summary_style": summary_style,
                "summary": summary,
                "timestamp": self._get_timestamp()
            }

        except Exception as e:
            error_msg = f"Failed to generate profile summary: {str(e)}"
            logger.error(error_msg)
            raise ToolExecutionError(error_msg)

    def _generate_friendly_summary(self, user_info: Dict[str, Any]) -> str:
        """Generate a friendly, conversational summary."""
        name = user_info.get("given_name") or user_info.get("name", "there")
        email = user_info.get("email", "")

        summary = f"Hi {name}! "

        if email:
            summary += f"I can see you're logged in with the email {email}. "
            if user_info.get("verified_email"):
                summary += "Your email is verified, which is great for security! "

        if user_info.get("picture"):
            summary += "I can see you have a profile picture set up too. "

        summary += "I'm here to help you with any questions or tasks you might have!"

        return summary

    def _generate_formal_summary(self, user_info: Dict[str, Any]) -> str:
        """Generate a formal, structured summary."""
        name = user_info.get("name", "User")
        email = user_info.get("email", "Not provided")

        summary = f"User Profile Summary:\n"
        summary += f"Name: {name}\n"
        summary += f"Email: {email}\n"

        if user_info.get("verified_email"):
            summary += "Email Status: Verified\n"
        else:
            summary += "Email Status: Unverified\n"

        if user_info.get("locale"):
            summary += f"Locale: {user_info['locale']}\n"

        summary += f"Authentication Provider: {user_info.get('iss', 'OAuth Provider')}"

        return summary

    def _generate_brief_summary(self, user_info: Dict[str, Any]) -> str:
        """Generate a brief, minimal summary."""
        name = user_info.get("name", "User")
        email = user_info.get("email", "")

        if email:
            return f"{name} ({email})"
        else:
            return name