"""
Shared test client utilities for testing authenticated agents
"""

import httpx
import json
import asyncio
import logging
import os
import subprocess
from typing import Dict, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class AuthenticatedTestClient:
    """Test client for making authenticated requests to agents."""

    def __init__(self, base_url: str, timeout: float = 30.0):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    async def test_health(self) -> Dict[str, Any]:
        """Test agent health endpoint."""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(f"{self.base_url}/health")
                return {
                    "success": response.status_code == 200,
                    "status_code": response.status_code,
                    "status": "healthy" if response.status_code == 200 else "unhealthy",
                    "response": response.json() if response.status_code == 200 else None
                }
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {
                "success": False,
                "status_code": 0,
                "status": "error",
                "error": str(e)
            }

    async def get_agent_card(self) -> Dict[str, Any]:
        """Get agent card from .well-known endpoint."""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(f"{self.base_url}/.well-known/agent-card.json")
                return {
                    "success": response.status_code == 200,
                    "status_code": response.status_code,
                    "agent_card": response.json() if response.status_code == 200 else None
                }
        except Exception as e:
            logger.error(f"Agent card fetch failed: {e}")
            return {
                "success": False,
                "status_code": 0,
                "error": str(e)
            }

    async def send_authenticated_message(
        self,
        message: str,
        bearer_token: Optional[str] = None,
        user_id: Optional[str] = None,
        oauth_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Send authenticated message to agent."""

        headers = {"Content-Type": "application/json"}

        # Add bearer token if provided
        if bearer_token:
            headers["Authorization"] = f"Bearer {bearer_token}"

        # Build A2A-compatible request payload
        payload = {
            "jsonrpc": "2.0",
            "id": "test-message-1",
            "method": "message/send",
            "params": {
                "message": {
                    "messageId": f"test-msg-{asyncio.current_task().get_name() if asyncio.current_task() else 'unknown'}",
                    "role": "user",
                    "parts": [{"text": message}]
                }
            }
        }

        # Add user context if provided
        if user_id:
            payload["params"]["user_id"] = user_id

        if oauth_context:
            payload["params"]["oauth_context"] = oauth_context

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/a2a",
                    headers=headers,
                    json=payload
                )

                result = {
                    "success": response.status_code == 200,
                    "status_code": response.status_code,
                    "raw_response": response.text
                }

                if response.status_code == 200:
                    try:
                        response_data = response.json()
                        result["response"] = response_data
                        result["message"] = response_data.get("result", {}).get("message", "")
                    except json.JSONDecodeError:
                        result["message"] = response.text

                return result

        except Exception as e:
            logger.error(f"Message send failed: {e}")
            return {
                "success": False,
                "status_code": 0,
                "error": str(e)
            }

    async def test_bearer_token_tool(self, test_token: str) -> Dict[str, Any]:
        """Test bearer token tool specifically."""
        message = f"Please use your bearer token tool to analyze this token: {test_token}"
        return await self.send_authenticated_message(message, bearer_token=test_token)

    async def test_auth_context_verification(
        self,
        target_agent: str,
        test_token: str
    ) -> Dict[str, Any]:
        """Test authentication context verification with a specific remote agent."""
        message = f"""
        Please delegate this task to the {target_agent}:
        Analyze my bearer token and confirm it was received with complete authentication context.
        Verify that the auth forwarding worked correctly.
        """
        return await self.send_authenticated_message(message, bearer_token=test_token)

    async def wait_for_agent_ready(self, max_retries: int = 10, delay: float = 2.0) -> bool:
        """Wait for agent to become ready (health check passes)."""
        for attempt in range(max_retries):
            health_result = await self.test_health()
            if health_result["success"]:
                logger.info(f"Agent at {self.base_url} is ready")
                return True

            logger.info(f"Agent not ready, attempt {attempt + 1}/{max_retries}, waiting {delay}s...")
            await asyncio.sleep(delay)

        logger.error(f"Agent at {self.base_url} failed to become ready after {max_retries} attempts")
        return False


class AgentServerManager:
    """Helper class to manage agent server lifecycle for testing."""

    def __init__(self, agent_module_path: str, port: int, agent_name: str):
        self.agent_module_path = Path(agent_module_path)
        self.port = port
        self.agent_name = agent_name
        self.process = None
        self.base_url = f"http://localhost:{port}"

    async def start_agent(self) -> bool:
        """Start the agent server."""
        try:
            # Import and start the agent
            import subprocess
            import sys

            cmd = [
                sys.executable,
                str(self.agent_module_path),
            ]

            env = {
                **dict(os.environ),
                f"{self.agent_name.upper()}_PORT": str(self.port),
                f"{self.agent_name.upper()}_HOST": "0.0.0.0"
            }

            self.process = subprocess.Popen(
                cmd,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )

            # Wait for server to start
            client = AuthenticatedTestClient(self.base_url)
            return await client.wait_for_agent_ready(max_retries=15, delay=2.0)

        except Exception as e:
            logger.error(f"Failed to start agent {self.agent_name}: {e}")
            return False

    async def stop_agent(self):
        """Stop the agent server."""
        if self.process:
            self.process.terminate()
            try:
                self.process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait()
            self.process = None

    async def __aenter__(self):
        success = await self.start_agent()
        if not success:
            raise RuntimeError(f"Failed to start agent {self.agent_name}")
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.stop_agent()