"""
Remote Agent Factory

This module provides functionality to optionally load and create remote agents
based on configuration files using official ADK A2A patterns.
"""

import os
import yaml
import logging
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


class RemoteAgentFactory:
    """
    Factory class for creating and managing remote agents based on configuration.

    Supports optional remote agent integration - if no configuration is found
    or if configuration is empty, returns empty list for standalone operation.
    """

    def __init__(self, config_dir: str = "config"):
        """
        Initialize the RemoteAgentFactory.

        Args:
            config_dir: Directory containing configuration files
        """
        self.config_dir = Path(config_dir)
        self.remote_config_path = self.config_dir / "remote_agents.yaml"

    async def load_remote_agents_if_configured(self) -> List[RemoteA2aAgent]:
        """
        Load remote agents only if configured, otherwise return empty list.

        Returns:
            List of RemoteA2aAgent instances, empty if no configuration or disabled
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

            # Create remote agents
            remote_agents = []
            for agent_config in remote_agents_config:
                if self._is_agent_enabled(agent_config):
                    try:
                        remote_agent = await self._create_remote_agent(agent_config)
                        remote_agents.append(remote_agent)
                        logger.info(f"Loaded remote agent: {remote_agent.name}")
                    except Exception as e:
                        logger.error(f"Failed to create remote agent {agent_config.get('name', 'unknown')}: {e}")
                        # Continue loading other agents even if one fails
                        continue
                else:
                    logger.info(f"Remote agent {agent_config.get('name', 'unknown')} is disabled")

            if remote_agents:
                logger.info(f"Successfully loaded {len(remote_agents)} remote agents")
            else:
                logger.info("No enabled remote agents found - running in single agent mode")

            return remote_agents

        except Exception as e:
            logger.error(f"Error loading remote agents configuration: {e}")
            logger.info("Falling back to single agent mode due to configuration error")
            return []

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

    async def _create_remote_agent(self, config: Dict[str, Any]) -> RemoteA2aAgent:
        """
        Create a RemoteA2aAgent from configuration.

        Args:
            config: Configuration dictionary containing agent details

        Returns:
            RemoteA2aAgent instance

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

        logger.debug(f"Creating remote agent: {name} with card URL: {agent_card_url}")

        return RemoteA2aAgent(
            name=name,
            description=description,
            agent_card=agent_card_url
        )

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
                    "description": "Example remote agent for demonstration",
                    "agent_card_url": "http://localhost:8002/a2a/example_agent",
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