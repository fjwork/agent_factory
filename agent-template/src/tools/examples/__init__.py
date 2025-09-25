"""
Example Tools for OAuth-Authenticated Agents

This package contains example implementations of authenticated tools that developers
can use as templates for building their own OAuth-enabled agent tools.
"""

from .profile_example_tool import ProfileExampleTool
from .api_example_tool import APIExampleTool

__all__ = ["ProfileExampleTool", "APIExampleTool"]