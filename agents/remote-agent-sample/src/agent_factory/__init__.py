"""
Agent Factory Module

This module provides factory classes for creating and managing agents,
including optional remote agent integration.
"""

from .remote_agent_factory import RemoteAgentFactory

__all__ = ["RemoteAgentFactory"]