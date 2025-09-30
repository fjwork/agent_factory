"""
Authenticated Remote Agent Factory

This module provides functionality to load and create remote agents with
authentication context forwarding using official ADK A2A patterns.
"""

import os
import yaml
import logging
import httpx
from typing import List, Dict, Any, Optional
from pathlib import Path

try:
    from google.adk.agents.remote_a2a_agent import RemoteA2aAgent
    from google.adk.agents.remote_a2a_agent import AGENT_CARD_WELL_KNOWN_PATH
except ImportError:
    # Fallback for development/testing
    class RemoteA2aAgent:
        def __init__(self, name: str, description: str, agent_card: str):
            self.name = name
            self.description = description
            self.agent_card = agent_card

    AGENT_CARD_WELL_KNOWN_PATH = "/.well-known/agent-card.json"

logger = logging.getLogger(__name__)


class AuthenticatedRemoteAgentFactory:
    """
    Factory class for creating and managing remote agents with authentication forwarding.

    This factory automatically forwards authentication context (bearer tokens, OAuth context)
    to remote agents via HTTP headers when delegating tasks. Supports optional remote agent
    integration - if no configuration is found or empty, returns empty list for standalone operation.
    """

    def __init__(self, config_dir: str = "config"):
        """
        Initialize the AuthenticatedRemoteAgentFactory.

        Args:
            config_dir: Directory containing configuration files
        """
        self.config_dir = Path(config_dir)
        self.remote_config_path = self.config_dir / "remote_agents.yaml"

    async def load_remote_agents_if_configured(self, auth_context: Optional[Dict[str, Any]] = None) -> List[RemoteA2aAgent]:
        """
        Load remote agents with authentication context forwarding, only if configured.

        Args:
            auth_context: Authentication context to forward to remote agents

        Returns:
            List of RemoteA2aAgent instances with auth forwarding, empty if no configuration or disabled
        """
        try:
            # Check if remote agents config file exists
            if not self.remote_config_path.exists():
                logger.info("No remote_agents.yaml found - running in single agent mode")
                return []

            # Load configuration
            config = self._load_config()
            if not config:
                logger.info("Empty or invalid remote_agents.yaml - running in single agent mode")
                return []

            # Check if remote agents are defined
            remote_agents_config = config.get("remote_agents", [])
            if not remote_agents_config:
                logger.info("No remote agents configured - running in single agent mode")
                return []

            # Create remote agents with auth forwarding
            remote_agents = []
            for agent_config in remote_agents_config:
                if self._is_agent_enabled(agent_config):
                    try:
                        remote_agent = await self._create_authenticated_remote_agent(agent_config, auth_context)
                        remote_agents.append(remote_agent)

                        # Log auth forwarding status
                        if auth_context and auth_context.get("authenticated"):
                            logger.info(f"Loaded remote agent with auth forwarding: {remote_agent.name}")
                        else:
                            logger.info(f"Loaded remote agent (no auth context): {remote_agent.name}")

                    except Exception as e:
                        logger.error(f"Failed to create remote agent {agent_config.get('name', 'unknown')}: {e}")
                        # Continue loading other agents even if one fails
                        continue
                else:
                    logger.info(f"Remote agent {agent_config.get('name', 'unknown')} is disabled")

            if remote_agents:
                auth_status = "with authentication forwarding" if auth_context and auth_context.get("authenticated") else "without authentication"
                logger.info(f"Successfully loaded {len(remote_agents)} remote agents {auth_status}")
            else:
                logger.info("No enabled remote agents found - running in single agent mode")

            return remote_agents

        except Exception as e:
            logger.error(f"Error loading remote agents configuration: {e}")
            logger.info("Falling back to single agent mode due to configuration error")
            return []

    async def _create_authenticated_remote_agent(self, config: Dict[str, Any], auth_context: Optional[Dict[str, Any]] = None) -> RemoteA2aAgent:
        """
        Create a RemoteA2aAgent with authentication context forwarding.

        Args:
            config: Configuration dictionary containing agent details
            auth_context: Authentication context to forward

        Returns:
            RemoteA2aAgent instance with auth headers configured

        Raises:
            ValueError: If required configuration fields are missing
        """
        # Validate required fields
        required_fields = ["name", "description", "agent_card_url"]
        for field in required_fields:
            if field not in config:
                raise ValueError(f"Missing required field '{field}' in remote agent configuration")

        name = config["name"]
        description = config["description"]
        agent_card_url = config["agent_card_url"]

        # Ensure agent card URL has the well-known path
        if not agent_card_url.endswith(AGENT_CARD_WELL_KNOWN_PATH):
            if agent_card_url.endswith('/'):
                agent_card_url = agent_card_url.rstrip('/') + AGENT_CARD_WELL_KNOWN_PATH
            else:
                agent_card_url = agent_card_url + AGENT_CARD_WELL_KNOWN_PATH

        logger.debug(f"Creating authenticated remote agent: {name} with card URL: {agent_card_url}")

        # Always create HTTP client (with or without auth headers)
        # This ensures _httpx_client attribute always exists for runtime updates
        if auth_context and auth_context.get("authenticated"):
            # Extract authentication token
            token = auth_context.get("token")
            auth_type = auth_context.get("auth_type", "bearer")

            if token:
                logger.debug(f"Configuring auth forwarding for {name}: {auth_type} token")

                # Create custom HTTP client with authentication headers
                headers = {
                    "Authorization": f"Bearer {token}",
                    "User-Agent": f"agent-template-root-agent/{name}",
                    "X-Forwarded-Auth-Type": auth_type
                }

                # Add additional context headers if available
                if auth_context.get("user_id"):
                    headers["X-Forwarded-User-ID"] = auth_context["user_id"]
                if auth_context.get("provider"):
                    headers["X-Forwarded-Auth-Provider"] = auth_context["provider"]

                # Create authenticated HTTP client
                http_client = httpx.AsyncClient(
                    timeout=30.0,
                    headers=headers,
                    follow_redirects=True
                )

                logger.info(f"Created authenticated HTTP client for {name} with bearer token forwarding")
            else:
                logger.warning(f"Auth context provided for {name} but no token found - creating default client")
                # Create default client (so _httpx_client attribute exists)
                http_client = httpx.AsyncClient(
                    timeout=30.0,
                    headers={"User-Agent": f"agent-template-root-agent/{name}"},
                    follow_redirects=True
                )
        else:
            logger.debug(f"No auth context for {name} - creating default client")
            # Always create a client so _httpx_client attribute exists for runtime updates
            http_client = httpx.AsyncClient(
                timeout=30.0,
                headers={"User-Agent": f"agent-template-root-agent/{name}"},
                follow_redirects=True
            )

        # Create the RemoteA2aAgent with httpx_client parameter (ADK supports this!)
        try:
            remote_agent = RemoteA2aAgent(
                name=name,
                description=description,
                agent_card=agent_card_url,
                httpx_client=http_client  # THIS IS THE FIX!
            )

            # Always have http_client now, log the auth status
            if auth_context and auth_context.get("authenticated") and auth_context.get("token"):
                logger.info(f"✅ Created {name} with authenticated HTTP client")
            else:
                logger.info(f"📱 Created {name} with default HTTP client (ready for runtime auth)")

        except Exception as e:
            logger.error(f"Failed to create RemoteA2aAgent: {e}")
            # Fallback: try without httpx_client but still create a default client
            try:
                remote_agent = RemoteA2aAgent(
                    name=name,
                    description=description,
                    agent_card=agent_card_url
                )
                logger.warning(f"Created {name} without httpx_client parameter (ADK version may not support it)")
                # Clean up the prepared client since we couldn't use it
                if http_client:
                    await http_client.aclose()
            except Exception as fallback_e:
                logger.error(f"Fallback creation also failed for {name}: {fallback_e}")
                # Clean up client and re-raise
                if http_client:
                    await http_client.aclose()
                raise

        return remote_agent

    def _load_config(self) -> Optional[Dict[str, Any]]:
        """
        Load the remote agents configuration from YAML file.

        Returns:
            Configuration dictionary or None if loading fails
        """
        try:
            with open(self.remote_config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
                return config if config else {}
        except yaml.YAMLError as e:
            logger.error(f"Invalid YAML in remote_agents.yaml: {e}")
            return None
        except Exception as e:
            logger.error(f"Error reading remote_agents.yaml: {e}")
            return None

    def _is_agent_enabled(self, agent_config: Dict[str, Any]) -> bool:
        """
        Check if a remote agent is enabled in configuration.

        Args:
            agent_config: Configuration dictionary for the agent

        Returns:
            True if agent is enabled, False otherwise
        """
        return agent_config.get("enabled", True)  # Default to enabled

    def get_config_template(self) -> Dict[str, Any]:
        """
        Get a template configuration for remote agents.

        Returns:
            Template configuration dictionary
        """
        return {
            "remote_agents": [
                {
                    "name": "example_remote_agent",
                    "description": "Example remote agent with authentication forwarding support",
                    "agent_card_url": "http://localhost:8002",
                    "enabled": True
                }
            ]
        }

    def create_sample_config(self, output_path: Optional[str] = None) -> str:
        """
        Create a sample remote agents configuration file.

        Args:
            output_path: Optional custom output path, defaults to config directory

        Returns:
            Path to the created configuration file
        """
        if output_path is None:
            output_path = self.remote_config_path
        else:
            output_path = Path(output_path)

        # Ensure parent directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)

        template = self.get_config_template()

        with open(output_path, 'w', encoding='utf-8') as f:
            yaml.dump(template, f, default_flow_style=False, indent=2)

        logger.info(f"Sample remote agents configuration created at: {output_path}")
        return str(output_path)

    def validate_config(self) -> Dict[str, Any]:
        """
        Validate the current remote agents configuration.

        Returns:
            Validation result dictionary with status and details
        """
        result = {
            "valid": False,
            "errors": [],
            "warnings": [],
            "agent_count": 0,
            "enabled_count": 0
        }

        try:
            if not self.remote_config_path.exists():
                result["warnings"].append("No remote_agents.yaml file found")
                result["valid"] = True  # Valid for standalone mode
                return result

            config = self._load_config()
            if not config:
                result["errors"].append("Configuration file is empty or invalid")
                return result

            remote_agents_config = config.get("remote_agents", [])
            result["agent_count"] = len(remote_agents_config)

            if not remote_agents_config:
                result["warnings"].append("No remote agents defined in configuration")
                result["valid"] = True  # Valid for standalone mode
                return result

            # Validate each agent configuration
            required_fields = ["name", "description", "agent_card_url"]

            for i, agent_config in enumerate(remote_agents_config):
                agent_name = agent_config.get("name", f"agent_{i}")

                # Check required fields
                for field in required_fields:
                    if field not in agent_config:
                        result["errors"].append(f"Agent '{agent_name}': Missing required field '{field}'")

                # Check if enabled
                if self._is_agent_enabled(agent_config):
                    result["enabled_count"] += 1

                # Validate URL format
                agent_card_url = agent_config.get("agent_card_url", "")
                if agent_card_url and not (agent_card_url.startswith("http://") or agent_card_url.startswith("https://")):
                    result["warnings"].append(f"Agent '{agent_name}': agent_card_url should be a full HTTP URL")

            result["valid"] = len(result["errors"]) == 0

            if result["enabled_count"] == 0:
                result["warnings"].append("No remote agents are enabled")

        except Exception as e:
            result["errors"].append(f"Validation error: {e}")

        return result


# Legacy alias for backward compatibility (will be removed in future versions)
RemoteAgentFactory = AuthenticatedRemoteAgentFactory