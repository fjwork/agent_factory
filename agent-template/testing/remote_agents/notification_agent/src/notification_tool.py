"""
Notification Tool for Remote Agent

This tool demonstrates bearer token/OAuth context forwarding in a remote agent.
It handles notification sending while verifying authentication context.
"""

import logging
from typing import Dict, Any, Optional
from google.adk.tools import ToolContext

logger = logging.getLogger(__name__)


class NotificationTool:
    """Tool for sending notifications that verifies authentication context."""

    def __init__(self):
        self.name = "notification_tool"
        self.description = "Sends notifications and verifies authentication context forwarding"

    async def execute_with_context(
        self,
        tool_context: ToolContext,
        notification_type: str = "email",
        recipient: str = "default@example.com",
        message: str = "Default notification message",
        **kwargs
    ) -> Dict[str, Any]:
        """
        Execute notification sending with authentication context verification.

        Args:
            tool_context: ADK ToolContext with session state
            notification_type: Type of notification (email, sms, push, slack)
            recipient: Notification recipient
            message: Message content
            **kwargs: Additional parameters

        Returns:
            Notification results with authentication verification
        """
        logger.info(f"🔔 Notification Tool - Sending {notification_type} to {recipient}")

        # Get authentication context from session state
        session_state = tool_context.state or {}

        # Handle State object vs dict
        if hasattr(session_state, '__dict__'):
            state_dict = vars(session_state)
        else:
            state_dict = session_state

        # Extract authentication information
        auth_info = self._extract_auth_info(state_dict)

        # Perform mock notification sending
        notification_result = self._send_notification(notification_type, recipient, message)

        # Combine notification with auth verification
        result = {
            "success": True,
            "tool": "notification_tool",
            "agent_type": "notification_agent",
            "notification_type": notification_type,
            "recipient": recipient,
            "message_sent": message,
            "notification_result": notification_result,
            "authentication_verification": auth_info,
            "message": f"✅ {notification_type.title()} notification sent to {recipient}. Authentication context received and verified.",
            "a2a_forwarding_test": "SUCCESS" if auth_info["authenticated"] else "FAILED"
        }

        logger.info(f"✅ Notification sent: {result}")
        return result

    def _extract_auth_info(self, state_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Extract authentication information from session state."""
        auth_info = {
            "authenticated": False,
            "auth_type": None,
            "user_id": None,
            "token_present": False,
            "oauth_context": {},
            "session_debug": {
                "state_type": type(state_dict).__name__,
                "session_keys": list(state_dict.keys()) if state_dict else [],
                "remote_agent": "notification_agent"
            }
        }

        # Check for OAuth context
        if state_dict.get("oauth_authenticated"):
            auth_info["authenticated"] = True
            auth_info["auth_type"] = "oauth"
            auth_info["user_id"] = state_dict.get("oauth_user_id")
            auth_info["token_present"] = bool(state_dict.get("oauth_token"))
            auth_info["oauth_context"] = {
                "provider": state_dict.get("oauth_provider"),
                "user_info": state_dict.get("oauth_user_info", {})
            }

        # Check for bearer token
        elif state_dict.get("oauth_token"):
            auth_info["authenticated"] = True
            auth_info["auth_type"] = "bearer"
            auth_info["token_present"] = True
            auth_info["user_id"] = state_dict.get("oauth_user_id", "bearer_user")

        return auth_info

    def _send_notification(self, notification_type: str, recipient: str, message: str) -> Dict[str, Any]:
        """Perform mock notification sending."""

        mock_results = {
            "email": {
                "status": "sent",
                "provider": "SendGrid",
                "message_id": "sg_msg_123456",
                "delivery_time": "2s"
            },
            "sms": {
                "status": "delivered",
                "provider": "Twilio",
                "message_id": "sms_msg_789012",
                "delivery_time": "1s"
            },
            "push": {
                "status": "pushed",
                "provider": "Firebase",
                "message_id": "fcm_msg_345678",
                "delivery_time": "0.5s"
            },
            "slack": {
                "status": "posted",
                "provider": "Slack API",
                "message_id": "slack_msg_901234",
                "delivery_time": "1.2s"
            },
            "default": {
                "status": "queued",
                "provider": "Generic",
                "message_id": "gen_msg_567890",
                "delivery_time": "3s"
            }
        }

        notification_result = mock_results.get(notification_type, mock_results["default"])

        return {
            "type": notification_type,
            "recipient": recipient,
            "message": message,
            "result": notification_result,
            "timestamp": "2025-01-26T12:00:00Z"
        }