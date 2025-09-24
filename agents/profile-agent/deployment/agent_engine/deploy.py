#!/usr/bin/env python3
"""
Agent Engine Deployment Script

This script deploys the ADK agent to Vertex AI Agent Engine.
"""

import os
import sys
import yaml
import logging
from typing import Dict, Any, Optional
import argparse

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

try:
    from google.cloud import aiplatform
    from google.cloud.aiplatform import gapic as aip
    VERTEX_AI_AVAILABLE = True
except ImportError:
    VERTEX_AI_AVAILABLE = False
    aiplatform = None
    aip = None

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AgentEngineDeployer:
    """Deploys ADK agents to Vertex AI Agent Engine."""

    def __init__(self, config_dir: str = "config", environment: str = "development"):
        if not VERTEX_AI_AVAILABLE:
            raise ImportError("Vertex AI SDK not available. Install google-cloud-aiplatform.")

        self.config_dir = config_dir
        self.environment = environment
        self.config = self._load_deployment_config()

        # Initialize Vertex AI
        project_id = self.config["deployment"]["env_vars"].get("GOOGLE_CLOUD_PROJECT")
        location = self.config["deployment"]["env_vars"].get("GOOGLE_CLOUD_LOCATION", "us-central1")

        aiplatform.init(project=project_id, location=location)

    def _load_deployment_config(self) -> Dict[str, Any]:
        """Load deployment configuration."""
        config_path = os.path.join(self.config_dir, "deployment_config.yaml")

        try:
            with open(config_path, 'r') as f:
                config_data = yaml.safe_load(f)

            # Apply environment-specific overrides
            if self.environment in config_data.get("environments", {}):
                env_overrides = config_data["environments"][self.environment]
                config_data = self._deep_merge(config_data, env_overrides)

            # Expand environment variables
            config_data = self._expand_env_vars(config_data)

            return config_data

        except Exception as e:
            logger.error(f"Failed to load deployment config: {e}")
            raise

    def create_agent(self) -> str:
        """Create a new agent in Agent Engine."""
        try:
            agent_config = self.config["agent_engine"]

            logger.info(f"🚀 Creating agent: {agent_config['display_name']}")

            # Prepare agent configuration
            agent_settings = self._prepare_agent_settings()

            # Create the agent
            agent = aiplatform.Agent.create(
                display_name=agent_config["display_name"],
                description=agent_config.get("description", "ADK Agent with OAuth authentication"),
                agent_settings=agent_settings
            )

            resource_id = agent.resource_name
            logger.info(f"✅ Agent created successfully!")
            logger.info(f"📍 Resource ID: {resource_id}")

            return resource_id

        except Exception as e:
            logger.error(f"❌ Agent creation failed: {e}")
            raise

    def update_agent(self, resource_id: str) -> str:
        """Update an existing agent."""
        try:
            logger.info(f"🔄 Updating agent: {resource_id}")

            # Get existing agent
            agent = aiplatform.Agent(resource_id)

            # Prepare updated settings
            agent_settings = self._prepare_agent_settings()

            # Update the agent
            agent.update(
                agent_settings=agent_settings
            )

            logger.info(f"✅ Agent updated successfully!")
            return resource_id

        except Exception as e:
            logger.error(f"❌ Agent update failed: {e}")
            raise

    def delete_agent(self, resource_id: str) -> bool:
        """Delete an agent."""
        try:
            logger.info(f"🗑️ Deleting agent: {resource_id}")

            agent = aiplatform.Agent(resource_id)
            agent.delete()

            logger.info(f"✅ Agent deleted successfully!")
            return True

        except Exception as e:
            logger.error(f"❌ Agent deletion failed: {e}")
            raise

    def list_agents(self) -> list:
        """List all agents in the project."""
        try:
            agents = aiplatform.Agent.list()

            logger.info(f"📋 Found {len(agents)} agents:")
            for agent in agents:
                logger.info(f"  - {agent.display_name}: {agent.resource_name}")

            return agents

        except Exception as e:
            logger.error(f"❌ Failed to list agents: {e}")
            raise

    def test_agent(self, resource_id: str, user_id: str = "test-user") -> Dict[str, Any]:
        """Test the deployed agent."""
        try:
            logger.info(f"🧪 Testing agent: {resource_id}")

            agent = aiplatform.Agent(resource_id)

            # Create a test session
            session = agent.create_session()

            # Send a test message
            test_message = "Hello, can you help me test the authentication?"
            response = session.send_message(test_message)

            logger.info(f"✅ Agent test successful!")
            logger.info(f"📤 Sent: {test_message}")
            logger.info(f"📥 Response: {response}")

            return {
                "success": True,
                "test_message": test_message,
                "response": response
            }

        except Exception as e:
            logger.error(f"❌ Agent test failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def _prepare_agent_settings(self) -> Dict[str, Any]:
        """Prepare agent settings for deployment."""
        agent_config = self.config["agent_engine"]

        # Basic agent configuration
        settings = {
            "model": agent_config["agent"]["model"],
            "temperature": agent_config["agent"].get("temperature", 0.7),
            "max_output_tokens": agent_config["agent"].get("max_output_tokens", 1024)
        }

        # Add tools configuration
        tools_config = agent_config.get("tools", {})
        if tools_config.get("enable_code_execution", False):
            settings["enable_code_execution"] = True

        if tools_config.get("enable_search", False):
            settings["enable_search"] = True

        # Add security configuration
        security_config = agent_config.get("security", {})
        if security_config.get("enable_authentication", False):
            settings["enable_authentication"] = True

        allowed_domains = security_config.get("allowed_domains")
        if allowed_domains:
            settings["allowed_domains"] = allowed_domains.split(",")

        # Add custom instructions from agent config
        agent_yaml_config = self._load_agent_config()
        if agent_yaml_config:
            agent_info = agent_yaml_config.get("agent", {})
            settings["instructions"] = f"""
You are {agent_info.get('name', 'an ADK agent')} with OAuth authentication capabilities.

{agent_info.get('description', 'I can help you with various tasks.')}

I have access to authenticated tools and can work with user credentials securely.
"""

        return settings

    def _load_agent_config(self) -> Optional[Dict[str, Any]]:
        """Load agent configuration for instructions."""
        config_path = os.path.join(self.config_dir, "agent_config.yaml")

        try:
            with open(config_path, 'r') as f:
                config_data = yaml.safe_load(f)

            # Apply environment-specific overrides
            if self.environment in config_data.get("environments", {}):
                env_overrides = config_data["environments"][self.environment]
                config_data = self._deep_merge(config_data, env_overrides)

            return config_data

        except Exception as e:
            logger.warning(f"Could not load agent config: {e}")
            return None

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


def main():
    """Main deployment function."""
    parser = argparse.ArgumentParser(description="Deploy ADK Agent to Vertex AI Agent Engine")
    parser.add_argument(
        "--action",
        choices=["create", "update", "delete", "list", "test"],
        default="create",
        help="Action to perform"
    )
    parser.add_argument(
        "--resource-id",
        help="Agent resource ID (required for update, delete, test)"
    )
    parser.add_argument(
        "--user-id",
        default="test-user",
        help="User ID for testing (default: test-user)"
    )
    parser.add_argument(
        "--environment",
        default="development",
        help="Deployment environment (development, staging, production)"
    )
    parser.add_argument(
        "--config-dir",
        default="config",
        help="Configuration directory"
    )

    args = parser.parse_args()

    try:
        deployer = AgentEngineDeployer(args.config_dir, args.environment)

        if args.action == "create":
            resource_id = deployer.create_agent()
            print(f"\n🎉 Agent created successfully!")
            print(f"📍 Resource ID: {resource_id}")

        elif args.action == "update":
            if not args.resource_id:
                print("❌ --resource-id required for update action")
                sys.exit(1)
            resource_id = deployer.update_agent(args.resource_id)
            print(f"\n🎉 Agent updated successfully!")
            print(f"📍 Resource ID: {resource_id}")

        elif args.action == "delete":
            if not args.resource_id:
                print("❌ --resource-id required for delete action")
                sys.exit(1)
            deployer.delete_agent(args.resource_id)
            print(f"\n🎉 Agent deleted successfully!")

        elif args.action == "list":
            agents = deployer.list_agents()
            print(f"\n📋 Total agents: {len(agents)}")

        elif args.action == "test":
            if not args.resource_id:
                print("❌ --resource-id required for test action")
                sys.exit(1)
            result = deployer.test_agent(args.resource_id, args.user_id)
            if result["success"]:
                print(f"\n🧪 Agent test successful!")
                print(f"📤 Test message: {result['test_message']}")
                print(f"📥 Response: {result['response']}")
            else:
                print(f"\n❌ Agent test failed: {result['error']}")

    except Exception as e:
        print(f"\n❌ Operation failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()