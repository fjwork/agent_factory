"""
Simplified Tools Module

Provides example authenticated tools for the simplified template.
"""

from .example_authenticated_tool import (
    ExampleAuthenticatedTool,
    BearerTokenValidationTool,
    create_authenticated_tools
)

__all__ = [
    "ExampleAuthenticatedTool",
    "BearerTokenValidationTool",
    "create_authenticated_tools"
]