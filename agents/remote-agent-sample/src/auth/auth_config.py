"""
Authentication Configuration Module

This module handles loading and managing OAuth and authentication configurations
from YAML files and environment variables.
"""

import os
import yaml
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class OAuthFlowType(Enum):
    """Supported OAuth flow types."""
    DEVICE_FLOW = "device_flow"
    AUTHORIZATION_CODE = "authorization_code"
    CLIENT_CREDENTIALS = "client_credentials"


class TokenStorageType(Enum):
    """Supported token storage types."""
    MEMORY = "memory"
    FILE = "file"
    SECRET_MANAGER = "secret_manager"


@dataclass
class OAuthEndpoints:
    """OAuth provider endpoints."""
    authorization_url: str
    token_url: str
    device_authorization_url: Optional[str] = None
    userinfo_url: Optional[str] = None
    jwks_url: Optional[str] = None


@dataclass
class OAuthProvider:
    """OAuth provider configuration."""
    name: str
    client_id: str
    client_secret: str
    endpoints: OAuthEndpoints
    default_scopes: List[str] = field(default_factory=list)
    extra_params: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SecurityScheme:
    """A2A security scheme configuration."""
    type: str
    description: Optional[str] = None
    parameters: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AuthConfig:
    """Main authentication configuration."""
    # OAuth settings
    default_provider: str
    flow_type: OAuthFlowType
    scopes: List[str]

    # Token management
    token_storage_type: TokenStorageType
    token_encryption: bool = True
    token_ttl_seconds: int = 3600

    # Security settings
    validate_issuer: bool = True
    validate_audience: bool = True
    require_https: bool = True
    token_introspection: bool = False

    # Providers
    providers: Dict[str, OAuthProvider] = field(default_factory=dict)

    # A2A security schemes
    a2a_security_schemes: Dict[str, SecurityScheme] = field(default_factory=dict)
    a2a_security: List[Dict[str, List[str]]] = field(default_factory=list)


class ConfigLoader:
    """Loads and manages authentication configuration."""

    def __init__(self, config_dir: str = "config"):
        self.config_dir = config_dir
        self._auth_config: Optional[AuthConfig] = None

    def load_config(self, environment: str = "development") -> AuthConfig:
        """Load authentication configuration for the specified environment."""
        if self._auth_config is not None:
            return self._auth_config

        oauth_config_path = os.path.join(self.config_dir, "oauth_config.yaml")

        try:
            with open(oauth_config_path, 'r') as f:
                config_data = yaml.safe_load(f)

            # Apply environment-specific overrides
            if environment in config_data.get("environments", {}):
                env_overrides = config_data["environments"][environment]
                config_data = self._deep_merge(config_data, env_overrides)

            # Expand environment variables
            config_data = self._expand_env_vars(config_data)

            # Parse OAuth configuration
            oauth_config = config_data.get("oauth", {})

            # Parse providers
            providers = {}
            for provider_name, provider_data in config_data.get("providers", {}).items():
                if not provider_data.get("client_id") or not provider_data.get("client_secret"):
                    logger.warning(f"Skipping provider {provider_name}: missing client_id or client_secret")
                    continue

                endpoints = OAuthEndpoints(
                    authorization_url=provider_data["authorization_url"],
                    token_url=provider_data["token_url"],
                    device_authorization_url=provider_data.get("device_authorization_url"),
                    userinfo_url=provider_data.get("userinfo_url"),
                    jwks_url=provider_data.get("jwks_url")
                )

                provider = OAuthProvider(
                    name=provider_name,
                    client_id=provider_data["client_id"],
                    client_secret=provider_data["client_secret"],
                    endpoints=endpoints,
                    default_scopes=provider_data.get("default_scopes", []),
                    extra_params={k: v for k, v in provider_data.items()
                                if k not in ["client_id", "client_secret", "authorization_url",
                                           "token_url", "device_authorization_url", "userinfo_url",
                                           "jwks_url", "default_scopes"]}
                )
                providers[provider_name] = provider

            # Parse A2A security schemes
            a2a_auth = config_data.get("a2a_auth", {})
            security_schemes = {}
            for scheme_name, scheme_data in a2a_auth.get("security_schemes", {}).items():
                security_schemes[scheme_name] = SecurityScheme(
                    type=scheme_data["type"],
                    description=scheme_data.get("description"),
                    parameters={k: v for k, v in scheme_data.items()
                              if k not in ["type", "description"]}
                )

            # Create main config
            self._auth_config = AuthConfig(
                default_provider=oauth_config.get("default_provider", "google"),
                flow_type=OAuthFlowType(oauth_config.get("flow_type", "device_flow")),
                scopes=oauth_config.get("scopes", "").split() if isinstance(oauth_config.get("scopes"), str) else oauth_config.get("scopes", []),
                token_storage_type=TokenStorageType(oauth_config.get("token_storage", {}).get("type", "memory")),
                token_encryption=oauth_config.get("token_storage", {}).get("encryption", True),
                token_ttl_seconds=oauth_config.get("token_storage", {}).get("ttl_seconds", 3600),
                validate_issuer=oauth_config.get("security", {}).get("validate_issuer", True),
                validate_audience=oauth_config.get("security", {}).get("validate_audience", True),
                require_https=oauth_config.get("security", {}).get("require_https", True),
                token_introspection=oauth_config.get("security", {}).get("token_introspection", False),
                providers=providers,
                a2a_security_schemes=security_schemes,
                a2a_security=a2a_auth.get("security", [])
            )

            logger.info(f"Loaded auth config for environment: {environment}")
            logger.info(f"Available providers: {list(providers.keys())}")

            return self._auth_config

        except Exception as e:
            logger.error(f"Failed to load authentication config: {e}")
            raise

    def get_provider(self, provider_name: Optional[str] = None) -> OAuthProvider:
        """Get OAuth provider configuration."""
        if self._auth_config is None:
            raise ValueError("Configuration not loaded. Call load_config() first.")

        provider_name = provider_name or self._auth_config.default_provider

        if provider_name not in self._auth_config.providers:
            raise ValueError(f"Provider '{provider_name}' not found in configuration")

        return self._auth_config.providers[provider_name]

    def get_security_schemes(self) -> Dict[str, SecurityScheme]:
        """Get A2A security schemes."""
        if self._auth_config is None:
            raise ValueError("Configuration not loaded. Call load_config() first.")

        return self._auth_config.a2a_security_schemes

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
_config_loader = ConfigLoader()


def load_auth_config(environment: str = None) -> AuthConfig:
    """Load authentication configuration."""
    env = environment or os.getenv("ENVIRONMENT", "development")
    return _config_loader.load_config(env)


def get_oauth_provider(provider_name: str = None) -> OAuthProvider:
    """Get OAuth provider configuration."""
    return _config_loader.get_provider(provider_name)


def get_security_schemes() -> Dict[str, SecurityScheme]:
    """Get A2A security schemes."""
    return _config_loader.get_security_schemes()