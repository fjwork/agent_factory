"""
Data Analysis Tool for Remote Agent

This tool demonstrates bearer token/OAuth context forwarding in a remote agent.
It performs basic data analysis while verifying authentication context.
"""

import logging
from typing import Dict, Any, Optional
from google.adk.tools import ToolContext

logger = logging.getLogger(__name__)


class DataAnalysisTool:
    """Tool for data analysis that verifies authentication context."""

    def __init__(self):
        self.name = "data_analysis_tool"
        self.description = "Performs data analysis and verifies authentication context forwarding"

    async def execute_with_context(
        self,
        tool_context: ToolContext,
        dataset_name: str = "default",
        analysis_type: str = "summary",
        **kwargs
    ) -> Dict[str, Any]:
        """
        Execute data analysis with authentication context verification.

        Args:
            tool_context: ADK ToolContext with session state
            dataset_name: Name of dataset to analyze
            analysis_type: Type of analysis to perform
            **kwargs: Additional parameters

        Returns:
            Analysis results with authentication verification
        """
        logger.info(f"🔍 Data Analysis Tool - Analyzing {dataset_name} ({analysis_type})")

        # Get authentication context from session state
        session_state = tool_context.state or {}

        # Handle State object vs dict
        if hasattr(session_state, '__dict__'):
            state_dict = vars(session_state)
        else:
            state_dict = session_state

        # Extract authentication information
        auth_info = self._extract_auth_info(state_dict)

        # Perform mock data analysis
        analysis_result = self._perform_analysis(dataset_name, analysis_type)

        # Combine analysis with auth verification
        result = {
            "success": True,
            "tool": "data_analysis_tool",
            "agent_type": "data_analysis_agent",
            "dataset": dataset_name,
            "analysis_type": analysis_type,
            "analysis_result": analysis_result,
            "authentication_verification": auth_info,
            "message": f"✅ Data analysis complete for {dataset_name}. Authentication context received and verified.",
            "a2a_forwarding_test": "SUCCESS" if auth_info["authenticated"] else "FAILED"
        }

        logger.info(f"✅ Data analysis completed: {result}")
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
                "remote_agent": "data_analysis_agent"
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

    def _perform_analysis(self, dataset_name: str, analysis_type: str) -> Dict[str, Any]:
        """Perform mock data analysis."""

        mock_data = {
            "sales_data": {
                "records": 1000,
                "total_revenue": 150000.50,
                "avg_order": 150.00,
                "top_product": "Widget A"
            },
            "user_data": {
                "total_users": 5000,
                "active_users": 3200,
                "conversion_rate": 0.64,
                "avg_session": 8.5
            },
            "default": {
                "records": 100,
                "status": "analyzed",
                "insights": ["Pattern A detected", "Anomaly at index 42"]
            }
        }

        dataset = mock_data.get(dataset_name, mock_data["default"])

        if analysis_type == "summary":
            return {
                "type": "summary",
                "dataset": dataset_name,
                "summary": dataset
            }
        elif analysis_type == "trends":
            return {
                "type": "trends",
                "dataset": dataset_name,
                "trends": ["Upward trend detected", "Seasonal pattern identified"],
                "confidence": 0.85
            }
        elif analysis_type == "forecast":
            return {
                "type": "forecast",
                "dataset": dataset_name,
                "forecast": {"next_period": "15% increase", "confidence": 0.75}
            }
        else:
            return {
                "type": analysis_type,
                "dataset": dataset_name,
                "result": f"Custom analysis '{analysis_type}' completed"
            }