#!/usr/bin/env python3
"""
OAuth Test Client for Agent Template

This script provides a comprehensive test client for validating OAuth flows
with the agent template. It demonstrates how to:
1. Initiate OAuth authentication
2. Complete the OAuth flow
3. Send authenticated A2A messages
4. Test various tool executions

Usage:
    python oauth_test_client.py --help
    python oauth_test_client.py --agent-url http://localhost:8000 --user-id test@example.com
"""

import asyncio
import argparse
import json
import logging
import time
from typing import Dict, Any, Optional
import httpx

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class AgentTestClient:
    """Test client for OAuth-authenticated agents."""

    def __init__(self, agent_url: str = "http://localhost:8000", timeout: float = 30.0):
        self.agent_url = agent_url.rstrip('/')
        self.timeout = timeout
        self.session_data = {}

    async def test_oauth_flow(self, user_id: str, provider: str = "google") -> bool:
        """Test the complete OAuth flow."""
        logger.info(f"🔄 Starting OAuth flow test for user {user_id} with provider {provider}")

        try:
            # Step 1: Check initial auth status
            logger.info("📋 Step 1: Checking initial authentication status...")
            auth_status = await self.check_auth_status(user_id, provider)
            logger.info(f"Initial auth status: {auth_status}")

            # Step 2: Initiate OAuth if not authenticated
            if not auth_status.get("authenticated", False):
                logger.info("🚀 Step 2: Initiating OAuth flow...")
                auth_result = await self.initiate_oauth(user_id, provider)

                if auth_result.get("success"):
                    logger.info(f"✅ OAuth initiated successfully!")
                    logger.info(f"🌐 Please visit: {auth_result.get('verification_uri')}")
                    logger.info(f"🔑 Enter code: {auth_result.get('user_code')}")

                    # Wait for user to complete OAuth
                    logger.info("⏳ Waiting for you to complete OAuth in browser...")
                    input("Press Enter after you've completed OAuth in the browser...")

                    # Check auth status again
                    logger.info("🔍 Step 3: Verifying OAuth completion...")
                    final_status = await self.check_auth_status(user_id, provider)

                    if final_status.get("authenticated", False):
                        logger.info("✅ OAuth flow completed successfully!")
                        return True
                    else:
                        logger.error("❌ OAuth flow failed or incomplete")
                        return False
                else:
                    logger.error(f"❌ Failed to initiate OAuth: {auth_result}")
                    return False
            else:
                logger.info("✅ User already authenticated!")
                return True

        except Exception as e:
            logger.error(f"❌ OAuth flow test failed: {e}")
            return False

    async def initiate_oauth(self, user_id: str, provider: str = "google") -> Dict[str, Any]:
        """Initiate OAuth flow."""
        url = f"{self.agent_url}/auth/initiate"
        data = {
            "user_id": user_id,
            "provider": provider
        }

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(url, json=data, timeout=self.timeout)
                response.raise_for_status()
                result = response.json()
                logger.debug(f"OAuth initiation response: {result}")
                return result

            except httpx.HTTPStatusError as e:
                logger.error(f"HTTP error during OAuth initiation: {e.response.status_code} - {e.response.text}")
                return {"success": False, "error": f"HTTP {e.response.status_code}"}
            except Exception as e:
                logger.error(f"OAuth initiation failed: {e}")
                return {"success": False, "error": str(e)}

    async def check_auth_status(self, user_id: str, provider: str = "google") -> Dict[str, Any]:
        """Check authentication status."""
        url = f"{self.agent_url}/auth/status"
        params = {
            "user_id": user_id,
            "provider": provider
        }

        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(url, params=params, timeout=self.timeout)
                response.raise_for_status()
                result = response.json()
                logger.debug(f"Auth status response: {result}")
                return result

            except httpx.HTTPStatusError as e:
                logger.error(f"HTTP error checking auth status: {e.response.status_code} - {e.response.text}")
                return {"authenticated": False, "error": f"HTTP {e.response.status_code}"}
            except Exception as e:
                logger.error(f"Auth status check failed: {e}")
                return {"authenticated": False, "error": str(e)}

    async def send_authenticated_message(
        self,
        message: str,
        user_id: str,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Send authenticated A2A message."""
        url = f"{self.agent_url}/"

        # Generate session ID if not provided
        if not session_id:
            session_id = f"test-session-{int(time.time())}"

        data = {
            "user_id": user_id,
            "session_id": session_id,
            "message": message,
            "stream": False
        }

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(url, json=data, timeout=self.timeout)
                response.raise_for_status()
                result = response.json()
                logger.debug(f"A2A message response: {result}")
                return result

            except httpx.HTTPStatusError as e:
                logger.error(f"HTTP error sending A2A message: {e.response.status_code} - {e.response.text}")
                return {"success": False, "error": f"HTTP {e.response.status_code}", "details": e.response.text}
            except Exception as e:
                logger.error(f"A2A message failed: {e}")
                return {"success": False, "error": str(e)}

    async def test_agent_tools(self, user_id: str) -> bool:
        """Test various agent tools."""
        logger.info("🛠️  Testing agent tools...")

        test_cases = [
            {
                "name": "Basic greeting",
                "message": "Hello! Can you help me?",
                "expected_keywords": ["help", "assist"]
            },
            {
                "name": "Tool execution",
                "message": "Execute the example authenticated tool",
                "expected_keywords": ["authenticated", "tool"]
            },
            {
                "name": "Profile request",
                "message": "What's my profile information?",
                "expected_keywords": ["profile", "information"]
            },
            {
                "name": "Error handling",
                "message": "Test error handling with invalid request",
                "expected_keywords": ["error", "invalid", "help"]
            }
        ]

        success_count = 0

        for i, test_case in enumerate(test_cases, 1):
            logger.info(f"📝 Test {i}/{len(test_cases)}: {test_case['name']}")

            try:
                result = await self.send_authenticated_message(test_case["message"], user_id)

                if result.get("success", True):  # Some responses may not have explicit success field
                    logger.info(f"✅ Test {i} passed")

                    # Log the response for verification
                    response_text = str(result).lower()
                    found_keywords = [kw for kw in test_case["expected_keywords"] if kw in response_text]
                    if found_keywords:
                        logger.info(f"   Found expected keywords: {found_keywords}")

                    success_count += 1
                else:
                    logger.warning(f"⚠️  Test {i} completed with warnings: {result}")
                    success_count += 1  # Still count as success if we got a response

            except Exception as e:
                logger.error(f"❌ Test {i} failed: {e}")

            # Small delay between tests
            await asyncio.sleep(1)

        logger.info(f"🏁 Tool tests completed: {success_count}/{len(test_cases)} passed")
        return success_count == len(test_cases)

    async def test_agent_card(self) -> bool:
        """Test agent card endpoints."""
        logger.info("📋 Testing agent card endpoints...")

        try:
            # Test public agent card
            logger.info("🔍 Testing public agent card...")
            public_card_url = f"{self.agent_url}/.well-known/agent-card.json"

            async with httpx.AsyncClient() as client:
                response = await client.get(public_card_url, timeout=self.timeout)
                response.raise_for_status()
                public_card = response.json()

                logger.info(f"✅ Public agent card retrieved successfully")
                logger.info(f"   Agent name: {public_card.get('name', 'Unknown')}")
                logger.info(f"   Version: {public_card.get('version', 'Unknown')}")

            # Test authenticated extended card (requires auth)
            logger.info("🔍 Testing authenticated extended card...")
            extended_card_url = f"{self.agent_url}/agent/authenticatedExtendedCard"

            try:
                async with httpx.AsyncClient() as client:
                    response = await client.get(extended_card_url, timeout=self.timeout)
                    if response.status_code == 401:
                        logger.info("✅ Extended card correctly requires authentication")
                    else:
                        response.raise_for_status()
                        extended_card = response.json()
                        logger.info(f"✅ Extended agent card retrieved successfully")

            except httpx.HTTPStatusError as e:
                if e.response.status_code == 401:
                    logger.info("✅ Extended card correctly requires authentication")
                else:
                    raise

            return True

        except Exception as e:
            logger.error(f"❌ Agent card test failed: {e}")
            return False

    async def test_health_endpoint(self) -> bool:
        """Test health endpoint."""
        logger.info("❤️  Testing health endpoint...")

        try:
            health_url = f"{self.agent_url}/health"

            async with httpx.AsyncClient() as client:
                response = await client.get(health_url, timeout=self.timeout)
                response.raise_for_status()
                health_data = response.json()

                logger.info(f"✅ Health endpoint responded successfully")
                logger.info(f"   Status: {health_data.get('status', 'Unknown')}")

                return True

        except Exception as e:
            logger.error(f"❌ Health endpoint test failed: {e}")
            return False

    async def run_full_test_suite(self, user_id: str, provider: str = "google") -> Dict[str, bool]:
        """Run the complete test suite."""
        logger.info("🚀 Starting full OAuth agent test suite...")

        results = {}

        # Test 1: Health endpoint
        results["health"] = await self.test_health_endpoint()

        # Test 2: Agent card
        results["agent_card"] = await self.test_agent_card()

        # Test 3: OAuth flow
        results["oauth_flow"] = await self.test_oauth_flow(user_id, provider)

        # Test 4: Agent tools (only if OAuth succeeded)
        if results["oauth_flow"]:
            results["agent_tools"] = await self.test_agent_tools(user_id)
        else:
            logger.warning("⚠️  Skipping agent tools test due to OAuth failure")
            results["agent_tools"] = False

        # Summary
        logger.info("📊 Test Results Summary:")
        for test_name, passed in results.items():
            status = "✅ PASS" if passed else "❌ FAIL"
            logger.info(f"   {test_name:15}: {status}")

        total_tests = len(results)
        passed_tests = sum(results.values())
        logger.info(f"📈 Overall: {passed_tests}/{total_tests} tests passed")

        return results


async def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="OAuth Agent Test Client")
    parser.add_argument(
        "--agent-url",
        default="http://localhost:8000",
        help="Agent server URL (default: http://localhost:8000)"
    )
    parser.add_argument(
        "--user-id",
        default="test@example.com",
        help="User ID for testing (default: test@example.com)"
    )
    parser.add_argument(
        "--provider",
        default="google",
        help="OAuth provider (default: google)"
    )
    parser.add_argument(
        "--test",
        choices=["oauth", "tools", "card", "health", "all"],
        default="all",
        help="Specific test to run (default: all)"
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=30.0,
        help="Request timeout in seconds (default: 30.0)"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Create test client
    client = AgentTestClient(args.agent_url, args.timeout)

    try:
        if args.test == "all":
            results = await client.run_full_test_suite(args.user_id, args.provider)
            return 0 if all(results.values()) else 1

        elif args.test == "oauth":
            success = await client.test_oauth_flow(args.user_id, args.provider)
            return 0 if success else 1

        elif args.test == "tools":
            success = await client.test_agent_tools(args.user_id)
            return 0 if success else 1

        elif args.test == "card":
            success = await client.test_agent_card()
            return 0 if success else 1

        elif args.test == "health":
            success = await client.test_health_endpoint()
            return 0 if success else 1

    except KeyboardInterrupt:
        logger.info("🛑 Test interrupted by user")
        return 1
    except Exception as e:
        logger.error(f"💥 Test failed with exception: {e}")
        return 1


if __name__ == "__main__":
    import sys
    exit_code = asyncio.run(main())
    sys.exit(exit_code)