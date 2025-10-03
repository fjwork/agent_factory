"""
Simplified Authentication Configuration Module

This module provides minimal authentication configuration for auth forwarding
without complex OAuth flows. Focuses on bearer token forwarding and ADK native auth.
"""

import os
import yaml
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class AuthType(Enum):
    """Supported authentication types."""
    BEARER_TOKEN = "bearer_token"
    API_KEY = "api_key"
    BASIC_AUTH = "basic_auth"
    NONE = "none"


@dataclass
class AuthContext:
    """Authentication context for forwarding to tools and remote agents."""
    auth_type: AuthType
    token: Optional[str] = None
    user_id: Optional[str] = None
    provider: Optional[str] = None
    headers: Dict[str, str] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_headers(self) -> Dict[str, str]:
        """Convert auth context to HTTP headers for forwarding."""
        headers = self.headers.copy()

        if self.token:
            if self.auth_type == AuthType.BEARER_TOKEN:
                headers["Authorization"] = f"Bearer {self.token}"
            elif self.auth_type == AuthType.API_KEY:
                headers["X-API-Key"] = self.token

        if self.user_id:
            headers["X-User-ID"] = self.user_id
        if self.provider:
            headers["X-Auth-Provider"] = self.provider

        headers["X-Auth-Type"] = self.auth_type.value

        return headers


@dataclass
class SimplifiedAuthConfig:
    """Simplified authentication configuration."""
    # Basic settings
    default_auth_type: AuthType = AuthType.BEARER_TOKEN
    require_https: bool = True

    # A2A forwarding settings
    forward_auth_headers: bool = True
    custom_headers: Dict[str, str] = field(default_factory=dict)

    # Security settings
    validate_tokens: bool = False  # Keep simple, no validation by default
    allowed_auth_types: List[AuthType] = field(default_factory=lambda: [AuthType.BEARER_TOKEN, AuthType.API_KEY])


class SimplifiedConfigLoader:
    """Loads simplified authentication configuration."""

    def __init__(self, config_dir: str = "config"):
        self.config_dir = config_dir
        self._auth_config: Optional[SimplifiedAuthConfig] = None

    def load_config(self, environment: str = "development") -> SimplifiedAuthConfig:
        """Load simplified authentication configuration."""
        if self._auth_config is not None:
            return self._auth_config

        config_path = os.path.join(self.config_dir, "auth_config.yaml")

        # Default configuration
        config_data = {
            "auth": {
                "default_type": "bearer_token",
                "require_https": True,
                "forward_headers": True,
                "validate_tokens": False
            }
        }

        # Try to load from file if it exists
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    file_config = yaml.safe_load(f)
                    if file_config:
                        config_data = self._deep_merge(config_data, file_config)
                logger.info(f"Loaded auth config from {config_path}")
            except Exception as e:
                logger.warning(f"Failed to load config file, using defaults: {e}")

        # Apply environment-specific overrides
        if environment in config_data.get("environments", {}):
            env_overrides = config_data["environments"][environment]
            config_data = self._deep_merge(config_data, env_overrides)

        # Expand environment variables
        config_data = self._expand_env_vars(config_data)

        # Parse configuration
        auth_config = config_data.get("auth", {})

        self._auth_config = SimplifiedAuthConfig(
            default_auth_type=AuthType(auth_config.get("default_type", "bearer_token")),
            require_https=auth_config.get("require_https", True),
            forward_auth_headers=auth_config.get("forward_headers", True),
            custom_headers=auth_config.get("custom_headers", {}),
            validate_tokens=auth_config.get("validate_tokens", False),
            allowed_auth_types=[AuthType(t) for t in auth_config.get("allowed_types", ["bearer_token", "api_key"])]
        )

        logger.info(f"Loaded simplified auth config for environment: {environment}")
        logger.info(f"Default auth type: {self._auth_config.default_auth_type.value}")

        return self._auth_config

    def _deep_merge(self, base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """Deep merge two dictionaries."""
        result = base.copy()

        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value

        return result

    def _expand_env_vars(self, obj: Any) -> Any:
        """Recursively expand environment variables in configuration."""
        if isinstance(obj, dict):
            return {k: self._expand_env_vars(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._expand_env_vars(item) for item in obj]
        elif isinstance(obj, str):
            return self._expand_env_var(obj)
        else:
            return obj

    def _expand_env_var(self, value: str) -> str:
        """Expand environment variables in a string value."""
        if not isinstance(value, str):
            return value

        # Handle ${VAR:default} syntax
        import re
        pattern = r'\$\{([^}:]+)(?::([^}]*))?\}'

        def replace_var(match):
            var_name = match.group(1)
            default_value = match.group(2) or ""
            return os.getenv(var_name, default_value)

        return re.sub(pattern, replace_var, value)


# Global config loader instance
_config_loader = SimplifiedConfigLoader()


def load_auth_config(environment: str = None) -> SimplifiedAuthConfig:
    """Load simplified authentication configuration."""
    env = environment or os.getenv("ENVIRONMENT", "development")
    return _config_loader.load_config(env)


def create_auth_context(
    auth_type: AuthType = AuthType.BEARER_TOKEN,
    token: str = None,
    user_id: str = None,
    provider: str = None,
    **metadata
) -> AuthContext:
    """Create authentication context for forwarding."""
    return AuthContext(
        auth_type=auth_type,
        token=token,
        user_id=user_id,
        provider=provider,
        metadata=metadata
    )


def extract_auth_from_request(request) -> Optional[AuthContext]:
    """Extract authentication context from an HTTP request."""
    try:
        # Check for Authorization header
        auth_header = request.headers.get("Authorization", "")

        if auth_header.startswith("Bearer "):
            token = auth_header[7:]  # Remove "Bearer " prefix
            return create_auth_context(
                auth_type=AuthType.BEARER_TOKEN,
                token=token,
                user_id=request.headers.get("X-User-ID"),
                provider=request.headers.get("X-Auth-Provider", "unknown")
            )

        # Check for API key
        api_key = request.headers.get("X-API-Key")
        if api_key:
            return create_auth_context(
                auth_type=AuthType.API_KEY,
                token=api_key,
                user_id=request.headers.get("X-User-ID"),
                provider=request.headers.get("X-Auth-Provider", "api_key")
            )

        # Check for Basic auth
        if auth_header.startswith("Basic "):
            return create_auth_context(
                auth_type=AuthType.BASIC_AUTH,
                token=auth_header,
                user_id=request.headers.get("X-User-ID"),
                provider=request.headers.get("X-Auth-Provider", "basic")
            )

        return None

    except Exception as e:
        logger.error(f"Failed to extract auth from request: {e}")
        return None