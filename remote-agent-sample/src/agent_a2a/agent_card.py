"""
Agent Card Generation Module

This module creates A2A Agent Cards with proper security schemes and capabilities.
"""

import os
import yaml
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
import logging

from a2a.types import (
    AgentCard, AgentSkill, AgentCapabilities, TransportProtocol,
    AgentProvider
)

from auth.auth_config import load_auth_config, get_security_schemes

logger = logging.getLogger(__name__)


@dataclass
class AgentCardConfig:
    """Configuration for agent card generation."""
    name: str
    version: str
    description: str
    url: str
    documentation_url: Optional[str] = None
    icon_url: Optional[str] = None
    provider_name: Optional[str] = None
    provider_url: Optional[str] = None


class AgentCardBuilder:
    """Builder for creating A2A Agent Cards with authentication."""

    def __init__(self, config_dir: str = "config"):
        self.config_dir = config_dir
        self.auth_config = load_auth_config()

    def load_agent_config(self, environment: str = "development") -> Dict[str, Any]:
        """Load agent configuration from YAML file."""
        config_path = os.path.join(self.config_dir, "agent_config.yaml")

        try:
            with open(config_path, 'r') as f:
                config_data = yaml.safe_load(f)

            # Apply environment-specific overrides
            if environment in config_data.get("environments", {}):
                env_overrides = config_data["environments"][environment]
                config_data = self._deep_merge(config_data, env_overrides)

            # Expand environment variables
            config_data = self._expand_env_vars(config_data)

            return config_data

        except Exception as e:
            logger.error(f"Failed to load agent config: {e}")
            raise

    def create_agent_card(self, environment: str = "development") -> AgentCard:
        """Create an A2A Agent Card with authentication schemes."""
        config = self.load_agent_config(environment)

        # Extract agent configuration
        agent_config = config.get("agent", {})
        a2a_config = config.get("a2a", {})
        skills_config = config.get("skills", [])

        # Create agent card configuration
        card_config = AgentCardConfig(
            name=agent_config.get("name", "MyAgent"),
            version=agent_config.get("version", "1.0.0"),
            description=agent_config.get("description", "ADK Agent with OAuth authentication"),
            url=a2a_config.get("agent_card", {}).get("url", "http://localhost:8000"),
            documentation_url=a2a_config.get("agent_card", {}).get("documentation_url"),
            icon_url=a2a_config.get("agent_card", {}).get("icon_url"),
            provider_name=a2a_config.get("agent_card", {}).get("provider", {}).get("name"),
            provider_url=a2a_config.get("agent_card", {}).get("provider", {}).get("url")
        )

        # Create capabilities
        capabilities_config = agent_config.get("capabilities", {})
        capabilities = AgentCapabilities(
            streaming=capabilities_config.get("streaming", True)
        )

        # Create skills
        skills = []
        for skill_config in skills_config:
            skill = AgentSkill(
                id=skill_config["id"],
                name=skill_config["name"],
                description=skill_config["description"],
                tags=skill_config.get("tags", []),
                examples=skill_config.get("examples", [])
            )
            skills.append(skill)

        # Create provider info
        provider = None
        if card_config.provider_name:
            provider = AgentProvider(
                organization=card_config.provider_name,
                url=card_config.provider_url or "https://example.com"
            )

        # Get security schemes from auth config
        security_schemes = self._convert_security_schemes()
        security = self._get_security_requirements()

        # Determine transport protocol
        transport_str = a2a_config.get("preferred_transport", "jsonrpc").lower()
        if transport_str == "jsonrpc":
            transport = TransportProtocol.jsonrpc
        elif transport_str == "http_json":
            transport = TransportProtocol.http_json
        else:
            transport = TransportProtocol.jsonrpc

        # Create Agent Card
        agent_card = AgentCard(
            name=card_config.name,
            version=card_config.version,
            description=card_config.description,
            url=card_config.url,
            documentation_url=card_config.documentation_url,
            icon_url=card_config.icon_url,
            provider=provider,
            capabilities=capabilities,
            default_input_modes=agent_config.get("input_modes", ["text/plain"]),
            default_output_modes=agent_config.get("output_modes", ["text/plain"]),
            preferred_transport=transport,
            skills=skills,
            security_schemes=security_schemes,
            security=security,
            supports_authenticated_extended_card=True
        )

        logger.info(f"Created agent card for {card_config.name} v{card_config.version}")
        logger.info(f"Security schemes: {list(security_schemes.keys()) if security_schemes else 'None'}")

        return agent_card

    def _convert_security_schemes(self) -> Optional[Dict[str, Any]]:
        """Convert auth config security schemes to A2A format."""
        try:
            security_schemes = get_security_schemes()
            if not security_schemes:
                return None

            a2a_schemes = {}

            for scheme_name, scheme in security_schemes.items():
                if scheme.type == "oauth2":
                    # OAuth2 security scheme
                    a2a_schemes[scheme_name] = {
                        "type": "oauth2",
                        "description": scheme.description or "OAuth 2.0 authentication",
                        "flows": {
                            "authorizationCode": {
                                "authorizationUrl": scheme.parameters.get("authorizationUrl", ""),
                                "tokenUrl": scheme.parameters.get("tokenUrl", ""),
                                "scopes": scheme.parameters.get("scopes", {})
                            }
                        }
                    }

                elif scheme.type == "http":
                    # HTTP Bearer authentication
                    a2a_schemes[scheme_name] = {
                        "type": "http",
                        "scheme": scheme.parameters.get("scheme", "bearer"),
                        "bearerFormat": scheme.parameters.get("bearerFormat", "JWT"),
                        "description": scheme.description or "Bearer token authentication"
                    }

                elif scheme.type == "apiKey":
                    # API Key authentication
                    a2a_schemes[scheme_name] = {
                        "type": "apiKey",
                        "in": scheme.parameters.get("in", "header"),
                        "name": scheme.parameters.get("name", "X-API-Key"),
                        "description": scheme.description or "API key authentication"
                    }

                else:
                    # Generic scheme
                    a2a_schemes[scheme_name] = {
                        "type": scheme.type,
                        "description": scheme.description or f"{scheme.type} authentication"
                    }
                    a2a_schemes[scheme_name].update(scheme.parameters)

            return a2a_schemes

        except Exception as e:
            logger.warning(f"Failed to convert security schemes: {e}")
            return None

    def _get_security_requirements(self) -> Optional[List[Dict[str, List[str]]]]:
        """Get security requirements from auth config."""
        try:
            if hasattr(self.auth_config, 'a2a_security') and self.auth_config.a2a_security:
                return self.auth_config.a2a_security

            # Default security requirement
            security_schemes = get_security_schemes()
            if security_schemes:
                # Require any one of the available schemes
                return [{scheme_name: []} for scheme_name in security_schemes.keys()]

            return None

        except Exception as e:
            logger.warning(f"Failed to get security requirements: {e}")
            return None

    def create_extended_agent_card(self, base_card: AgentCard, user_context: Dict[str, Any]) -> AgentCard:
        """Create an extended agent card with user-specific information."""
        # This could include user-specific skills, enhanced descriptions, etc.
        # For now, we'll return the same card but this can be extended

        extended_card = AgentCard(
            name=base_card.name,
            version=base_card.version,
            description=f"{base_card.description} (Extended for user)",
            url=base_card.url,
            documentation_url=base_card.documentation_url,
            icon_url=base_card.icon_url,
            provider=base_card.provider,
            capabilities=base_card.capabilities,
            default_input_modes=base_card.default_input_modes,
            default_output_modes=base_card.default_output_modes,
            preferred_transport=base_card.preferred_transport,
            skills=base_card.skills,  # Could be filtered based on user permissions
            security_schemes=base_card.security_schemes,
            security=base_card.security,
            supports_authenticated_extended_card=True
        )

        logger.info(f"Created extended agent card for user context: {user_context.get('user_id', 'unknown')}")
        return extended_card

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


def create_agent_card(environment: str = "development", config_dir: str = "config") -> AgentCard:
    """Factory function to create an agent card."""
    builder = AgentCardBuilder(config_dir)
    return builder.create_agent_card(environment)