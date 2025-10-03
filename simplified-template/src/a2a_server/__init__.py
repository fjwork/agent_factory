"""
Simplified A2A Server Module

Provides HTTPS-enabled A2A server with auth forwarding capabilities.
"""

from .server import (
    SimplifiedA2AServer,
    SimplifiedA2ARequestHandler,
    create_simplified_a2a_server,
    create_https_uvicorn_config
)

__all__ = [
    "SimplifiedA2AServer",
    "SimplifiedA2ARequestHandler",
    "create_simplified_a2a_server",
    "create_https_uvicorn_config"
]