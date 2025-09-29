"""
Approval Tool for Remote Agent

This tool demonstrates bearer token/OAuth context forwarding in a remote agent.
It handles approval workflows and human-in-the-loop processes while verifying authentication context.
"""

import logging
from typing import Dict, Any, Optional
from google.adk.tools import ToolContext

logger = logging.getLogger(__name__)


class ApprovalTool:
    """Tool for handling approvals that verifies authentication context."""

    def __init__(self):
        self.name = "approval_tool"
        self.description = "Handles approval workflows and verifies authentication context forwarding"

    async def execute_with_context(
        self,
        tool_context: ToolContext,
        approval_type: str = "document",
        item_id: str = "default-item-123",
        action: str = "request_approval",
        approver: str = "manager@example.com",
        **kwargs
    ) -> Dict[str, Any]:
        """
        Execute approval workflow with authentication context verification.

        Args:
            tool_context: ADK ToolContext with session state
            approval_type: Type of approval (document, expense, access, workflow)
            item_id: ID of item requiring approval
            action: Action to perform (request_approval, approve, reject, escalate)
            approver: Assigned approver
            **kwargs: Additional parameters

        Returns:
            Approval results with authentication verification
        """
        logger.info(f"✋ Approval Tool - {action} for {approval_type} ({item_id})")

        # Get authentication context from session state
        session_state = tool_context.state or {}

        # Handle State object vs dict
        if hasattr(session_state, '__dict__'):
            state_dict = vars(session_state)
        else:
            state_dict = session_state

        # Extract authentication information
        auth_info = self._extract_auth_info(state_dict)

        # Perform mock approval processing
        approval_result = self._process_approval(approval_type, item_id, action, approver)

        # Combine approval with auth verification
        result = {
            "success": True,
            "tool": "approval_tool",
            "agent_type": "approval_agent",
            "approval_type": approval_type,
            "item_id": item_id,
            "action": action,
            "approver": approver,
            "approval_result": approval_result,
            "authentication_verification": auth_info,
            "message": f"✅ {action.replace('_', ' ').title()} processed for {approval_type} {item_id}. Authentication context received and verified.",
            "a2a_forwarding_test": "SUCCESS" if auth_info["authenticated"] else "FAILED"
        }

        logger.info(f"✅ Approval processed: {result}")
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
                "remote_agent": "approval_agent"
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

    def _process_approval(self, approval_type: str, item_id: str, action: str, approver: str) -> Dict[str, Any]:
        """Perform mock approval processing."""

        approval_workflows = {
            "document": {
                "workflow_id": "doc_workflow_001",
                "steps": ["review", "approve", "publish"],
                "estimated_time": "2-3 business days"
            },
            "expense": {
                "workflow_id": "exp_workflow_002",
                "steps": ["validate", "budget_check", "approve"],
                "estimated_time": "1-2 business days"
            },
            "access": {
                "workflow_id": "access_workflow_003",
                "steps": ["security_review", "manager_approve", "provision"],
                "estimated_time": "4-6 hours"
            },
            "workflow": {
                "workflow_id": "meta_workflow_004",
                "steps": ["design_review", "stakeholder_approve", "deploy"],
                "estimated_time": "1 week"
            }
        }

        workflow = approval_workflows.get(approval_type, approval_workflows["document"])

        if action == "request_approval":
            return {
                "action": "approval_requested",
                "item_id": item_id,
                "workflow": workflow,
                "status": "pending",
                "approver": approver,
                "created_at": "2025-01-26T12:00:00Z",
                "due_date": "2025-01-28T17:00:00Z"
            }
        elif action == "approve":
            return {
                "action": "approved",
                "item_id": item_id,
                "status": "approved",
                "approver": approver,
                "approved_at": "2025-01-26T12:30:00Z",
                "comments": "Approved after review"
            }
        elif action == "reject":
            return {
                "action": "rejected",
                "item_id": item_id,
                "status": "rejected",
                "approver": approver,
                "rejected_at": "2025-01-26T12:30:00Z",
                "reason": "Does not meet approval criteria"
            }
        elif action == "escalate":
            return {
                "action": "escalated",
                "item_id": item_id,
                "status": "escalated",
                "escalated_to": "senior_manager@example.com",
                "escalated_at": "2025-01-26T12:30:00Z",
                "reason": "Requires higher level approval"
            }
        else:
            return {
                "action": action,
                "item_id": item_id,
                "status": "processing",
                "message": f"Custom approval action '{action}' initiated"
            }