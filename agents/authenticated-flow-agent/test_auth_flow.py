"""
Test Authentication Flow

This script tests the end-to-end authentication flow for the authenticated-flow-agent.
"""

import asyncio
import httpx
import json
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AuthFlowTester:
    """Test authentication flow end-to-end."""

    def __init__(self, orchestrator_url: str = "http://localhost:8001", remote_url: str = "http://localhost:8002"):
        self.orchestrator_url = orchestrator_url
        self.remote_url = remote_url

    async def test_health_endpoints(self):
        """Test that both agents are running."""
        logger.info("🔍 Testing health endpoints...")

        async with httpx.AsyncClient() as client:
            try:
                # Test orchestrator health
                response = await client.get(f"{self.orchestrator_url}/health")
                if response.status_code == 200:
                    logger.info("✅ Orchestrator agent is healthy")
                else:
                    logger.error(f"❌ Orchestrator health check failed: {response.status_code}")
                    return False

                # Test remote agent health
                response = await client.get(f"{self.remote_url}/health")
                if response.status_code == 200:
                    logger.info("✅ Remote agent is healthy")
                else:
                    logger.error(f"❌ Remote agent health check failed: {response.status_code}")
                    return False

                return True

            except Exception as e:
                logger.error(f"❌ Health check failed: {e}")
                return False

    async def test_agent_cards(self):
        """Test that agent cards are accessible."""
        logger.info("🔍 Testing agent cards...")

        async with httpx.AsyncClient() as client:
            try:
                # Test orchestrator agent card
                response = await client.get(f"{self.orchestrator_url}/.well-known/agent-card.json")
                if response.status_code == 200:
                    card_data = response.json()
                    logger.info(f"✅ Orchestrator agent card: {card_data.get('name', 'Unknown')}")
                else:
                    logger.error(f"❌ Orchestrator agent card failed: {response.status_code}")
                    return False

                # Test remote agent card
                response = await client.get(f"{self.remote_url}/.well-known/agent-card.json")
                if response.status_code == 200:
                    card_data = response.json()
                    logger.info(f"✅ Remote agent card: {card_data.get('name', 'Unknown')}")
                else:
                    logger.error(f"❌ Remote agent card failed: {response.status_code}")
                    return False

                return True

            except Exception as e:
                logger.error(f"❌ Agent card test failed: {e}")
                return False

    async def test_bearer_token_auth(self):
        """Test bearer token authentication."""
        logger.info("🔍 Testing bearer token authentication...")

        # Test bearer token
        test_token = "test-bearer-token-12345"

        message_request = {
            "jsonrpc": "2.0",
            "id": "test-001",
            "method": "message/send",
            "params": {
                "message": {
                    "role": "user",
                    "content": [{"text": "Test local authentication with bearer token"}]
                }
            }
        }

        headers = {
            "Authorization": f"Bearer {test_token}",
            "Content-Type": "application/json"
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.post(
                    f"{self.orchestrator_url}/",
                    json=message_request,
                    headers=headers
                )

                if response.status_code == 200:
                    result = response.json()
                    logger.info("✅ Bearer token authentication successful")
                    logger.info(f"Response: {json.dumps(result, indent=2)}")
                    return True
                else:
                    logger.error(f"❌ Bearer token authentication failed: {response.status_code}")
                    logger.error(f"Response: {response.text}")
                    return False

            except Exception as e:
                logger.error(f"❌ Bearer token test failed: {e}")
                return False

    async def test_remote_delegation(self):
        """Test delegation to remote agent."""
        logger.info("🔍 Testing remote agent delegation...")

        test_token = "test-bearer-token-remote-12345"

        message_request = {
            "jsonrpc": "2.0",
            "id": "test-002",
            "method": "message/send",
            "params": {
                "message": {
                    "role": "user",
                    "content": [{"text": "Test remote authentication by delegating to the remote agent"}]
                }
            }
        }

        headers = {
            "Authorization": f"Bearer {test_token}",
            "Content-Type": "application/json"
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            try:
                response = await client.post(
                    f"{self.orchestrator_url}/",
                    json=message_request,
                    headers=headers
                )

                if response.status_code == 200:
                    result = response.json()
                    logger.info("✅ Remote delegation successful")
                    logger.info(f"Response: {json.dumps(result, indent=2)}")
                    return True
                else:
                    logger.error(f"❌ Remote delegation failed: {response.status_code}")
                    logger.error(f"Response: {response.text}")
                    return False

            except Exception as e:
                logger.error(f"❌ Remote delegation test failed: {e}")
                return False

    async def test_auth_status_endpoints(self):
        """Test authentication status endpoints."""
        logger.info("🔍 Testing authentication status endpoints...")

        async with httpx.AsyncClient() as client:
            try:
                # Test orchestrator auth status
                response = await client.get(f"{self.orchestrator_url}/auth/dual-status")
                if response.status_code == 200:
                    status_data = response.json()
                    logger.info("✅ Orchestrator auth status accessible")
                    logger.info(f"Auth status: {json.dumps(status_data, indent=2)}")
                else:
                    logger.warning(f"⚠️ Orchestrator auth status: {response.status_code}")

                # Test remote agent auth status
                response = await client.get(f"{self.remote_url}/auth/dual-status")
                if response.status_code == 200:
                    status_data = response.json()
                    logger.info("✅ Remote agent auth status accessible")
                    logger.info(f"Auth status: {json.dumps(status_data, indent=2)}")
                else:
                    logger.warning(f"⚠️ Remote agent auth status: {response.status_code}")

                return True

            except Exception as e:
                logger.error(f"❌ Auth status test failed: {e}")
                return False

    async def run_all_tests(self):
        """Run all authentication flow tests."""
        logger.info("🚀 Starting authentication flow tests...")
        logger.info(f"Orchestrator: {self.orchestrator_url}")
        logger.info(f"Remote Agent: {self.remote_url}")
        logger.info("-" * 60)

        results = []

        # Test 1: Health checks
        results.append(await self.test_health_endpoints())

        # Test 2: Agent cards
        results.append(await self.test_agent_cards())

        # Test 3: Auth status endpoints
        results.append(await self.test_auth_status_endpoints())

        # Test 4: Bearer token authentication
        results.append(await self.test_bearer_token_auth())

        # Test 5: Remote delegation
        results.append(await self.test_remote_delegation())

        # Summary
        logger.info("-" * 60)
        passed = sum(results)
        total = len(results)

        if passed == total:
            logger.info(f"🎉 All tests passed! ({passed}/{total})")
        else:
            logger.info(f"⚠️ {passed}/{total} tests passed")

        return passed == total


async def main():
    """Main test function."""
    tester = AuthFlowTester()
    success = await tester.run_all_tests()

    if success:
        logger.info("✅ Authentication flow verification complete!")
    else:
        logger.error("❌ Some tests failed. Check logs above.")


if __name__ == "__main__":
    asyncio.run(main())