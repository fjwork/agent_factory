#!/usr/bin/env python3
"""
Cloud Run Deployment Script

This script deploys the ADK agent to Google Cloud Run with proper configuration.
"""

import os
import sys
import yaml
import subprocess
import logging
from typing import Dict, Any, List, Optional
import argparse

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CloudRunDeployer:
    """Deploys ADK agents to Google Cloud Run."""

    def __init__(self, config_dir: str = "config", environment: str = "development"):
        self.config_dir = config_dir
        self.environment = environment
        self.config = self._load_deployment_config()

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

    def deploy(self, build_image: bool = True) -> str:
        """Deploy to Cloud Run."""
        try:
            # Validate prerequisites
            self._validate_prerequisites()

            # Build and push image if requested
            if build_image:
                image_url = self._build_and_push_image()
            else:
                image_url = self._get_image_url()

            # Deploy to Cloud Run
            service_url = self._deploy_to_cloud_run(image_url)

            logger.info(f"✅ Deployment successful!")
            logger.info(f"🌐 Service URL: {service_url}")

            return service_url

        except Exception as e:
            logger.error(f"❌ Deployment failed: {e}")
            raise

    def _validate_prerequisites(self):
        """Validate prerequisites for deployment."""
        # Check if gcloud is installed and authenticated
        try:
            result = subprocess.run(
                ["gcloud", "auth", "list", "--filter=status:ACTIVE", "--format=value(account)"],
                capture_output=True,
                text=True,
                check=True
            )
            if not result.stdout.strip():
                raise Exception("No active gcloud authentication found. Run 'gcloud auth login'")

        except subprocess.CalledProcessError:
            raise Exception("gcloud CLI not found or not authenticated")

        # Check if project is set
        project_id = self.config["deployment"]["env_vars"].get("GOOGLE_CLOUD_PROJECT")
        if not project_id:
            raise Exception("GOOGLE_CLOUD_PROJECT not set")

        # Check if required APIs are enabled
        self._check_apis_enabled(project_id)

    def _check_apis_enabled(self, project_id: str):
        """Check if required APIs are enabled."""
        required_apis = [
            "run.googleapis.com",
            "artifactregistry.googleapis.com",
            "secretmanager.googleapis.com"
        ]

        for api in required_apis:
            try:
                result = subprocess.run(
                    ["gcloud", "services", "list", "--enabled", f"--filter=name:{api}", "--format=value(name)"],
                    capture_output=True,
                    text=True,
                    check=True
                )
                if api not in result.stdout:
                    logger.info(f"Enabling API: {api}")
                    subprocess.run(
                        ["gcloud", "services", "enable", api],
                        check=True
                    )
            except subprocess.CalledProcessError as e:
                logger.warning(f"Could not check/enable API {api}: {e}")

    def _build_and_push_image(self) -> str:
        """Build and push container image."""
        deployment_config = self.config["deployment"]
        image_config = deployment_config["image"]

        # Build image URL
        image_url = f"{image_config['registry']}/{image_config['project_id']}/{image_config['name']}:{image_config['tag']}"

        logger.info(f"🔨 Building image: {image_url}")

        # Build image
        build_cmd = [
            "gcloud", "builds", "submit",
            "--tag", image_url,
            "--file", "deployment/docker/Dockerfile",
            "."
        ]

        try:
            subprocess.run(build_cmd, check=True)
            logger.info(f"✅ Image built successfully: {image_url}")
            return image_url

        except subprocess.CalledProcessError as e:
            logger.error(f"❌ Image build failed: {e}")
            raise

    def _get_image_url(self) -> str:
        """Get image URL without building."""
        deployment_config = self.config["deployment"]
        image_config = deployment_config["image"]

        return f"{image_config['registry']}/{image_config['project_id']}/{image_config['name']}:{image_config['tag']}"

    def _deploy_to_cloud_run(self, image_url: str) -> str:
        """Deploy to Cloud Run."""
        cloud_run_config = self.config["cloud_run"]

        logger.info(f"🚀 Deploying to Cloud Run: {cloud_run_config['service_name']}")

        # Build deployment command
        deploy_cmd = [
            "gcloud", "run", "deploy", cloud_run_config["service_name"],
            "--image", image_url,
            "--region", cloud_run_config["region"],
            "--platform", "managed"
        ]

        # Add resource configuration
        resources = cloud_run_config.get("resources", {})
        if "cpu" in resources:
            deploy_cmd.extend(["--cpu", str(resources["cpu"])])
        if "memory" in resources:
            deploy_cmd.extend(["--memory", resources["memory"]])
        if "max_instances" in resources:
            deploy_cmd.extend(["--max-instances", str(resources["max_instances"])])
        if "min_instances" in resources:
            deploy_cmd.extend(["--min-instances", str(resources["min_instances"])])

        # Add service configuration
        service_config = cloud_run_config.get("service", {})
        if service_config.get("allow_unauthenticated", False):
            deploy_cmd.append("--allow-unauthenticated")
        if "timeout" in service_config:
            deploy_cmd.extend(["--timeout", str(service_config["timeout"])])

        # Add environment variables
        env_vars = self._prepare_env_vars()
        if env_vars:
            deploy_cmd.extend(["--set-env-vars", ",".join(env_vars)])

        # Add secrets
        secrets = self._prepare_secrets()
        if secrets:
            for secret in secrets:
                deploy_cmd.extend(["--set-secrets", secret])

        # Add annotations
        annotations = cloud_run_config.get("annotations", {})
        for key, value in annotations.items():
            if value:  # Only add non-empty annotations
                deploy_cmd.extend(["--set-annotations", f"{key}={value}"])

        # Execute deployment
        try:
            result = subprocess.run(deploy_cmd, capture_output=True, text=True, check=True)

            # Extract service URL from output
            lines = result.stderr.split('\n')
            service_url = None
            for line in lines:
                if 'Service URL:' in line:
                    service_url = line.split('Service URL:')[1].strip()
                    break

            if not service_url:
                # Fallback: construct URL
                service_url = f"https://{cloud_run_config['service_name']}-{cloud_run_config['region']}.run.app"

            return service_url

        except subprocess.CalledProcessError as e:
            logger.error(f"❌ Cloud Run deployment failed: {e}")
            logger.error(f"Error output: {e.stderr}")
            raise

    def _prepare_env_vars(self) -> List[str]:
        """Prepare environment variables for deployment."""
        env_vars = []
        deployment_env_vars = self.config["deployment"].get("env_vars", {})

        for key, value in deployment_env_vars.items():
            if value:  # Only add non-empty values
                env_vars.append(f"{key}={value}")

        return env_vars

    def _prepare_secrets(self) -> List[str]:
        """Prepare secrets configuration for deployment."""
        secrets = []
        deployment_secrets = self.config["deployment"].get("secrets", {})

        for env_var, secret_name in deployment_secrets.items():
            if secret_name:  # Only add non-empty secrets
                secrets.append(f"{env_var}={secret_name}:latest")

        return secrets

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
    parser = argparse.ArgumentParser(description="Deploy ADK Agent to Cloud Run")
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
    parser.add_argument(
        "--no-build",
        action="store_true",
        help="Skip image building (use existing image)"
    )

    args = parser.parse_args()

    try:
        deployer = CloudRunDeployer(args.config_dir, args.environment)
        service_url = deployer.deploy(build_image=not args.no_build)

        print(f"\n🎉 Deployment completed successfully!")
        print(f"📍 Service URL: {service_url}")
        print(f"🔍 Agent Card: {service_url}/.well-known/agent-card.json")
        print(f"💚 Health Check: {service_url}/health")

    except Exception as e:
        print(f"\n❌ Deployment failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()