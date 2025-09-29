"""
Test script for approval remote agent

This script tests:
1. Agent server startup and health
2. Agent card accessibility
3. Bearer token context verification
4. Approval tool functionality
5. Authentication forwarding verification
"""

import asyncio
import logging
import os
import sys
import subprocess
from pathlib import Path

# Add src and testing to path
project_root = Path(__file__).parent.parent.parent
src_dir = project_root / "src"
testing_dir = project_root / "testing"
sys.path.insert(0, str(src_dir))
sys.path.insert(0, str(testing_dir))

from utils.test_client import AuthenticatedTestClient
from utils.auth_test_utils import BearerTokenGenerator, AuthAssertions

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class ApprovalAgentTester:
    """Test suite for the approval remote agent."""

    def __init__(self, port: int = 8004):
        self.port = port
        self.host = "localhost"
        self.base_url = f"http://{self.host}:{self.port}"
        self.agent_name = "approval_agent"
        self.agent_module_path = project_root / "testing" / "remote_agents" / "approval_agent" / "src" / "agent.py"
        self.process = None
        self.token_generator = BearerTokenGenerator()

    async def start_agent_server(self) -> bool:
        """Start the approval agent server."""
        print(f"🚀 Starting Approval Agent on {self.host}:{self.port}")

        try:
            # Set environment variables
            env = dict(os.environ)
            env["APPROVAL_PORT"] = str(self.port)
            env["APPROVAL_HOST"] = self.host
            env["LOG_LEVEL"] = "INFO"

            # Start the agent process
            self.process = subprocess.Popen(
                [sys.executable, str(self.agent_module_path)],
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )

            # Wait for server to start
            client = AuthenticatedTestClient(self.base_url)
            started = await client.wait_for_agent_ready(max_retries=15, delay=2.0)

            if started:
                print(f"✅ Approval Agent started successfully")
                print(f"📋 Agent Card: {self.base_url}/.well-known/agent-card.json")
                print(f"🔍 A2A Endpoint: {self.base_url}/a2a/{self.agent_name}")
                return True
            else:
                print(f"❌ Failed to start Approval Agent")
                return False

        except Exception as e:
            logger.error(f"Failed to start approval agent: {e}")
            return False

    async def stop_agent_server(self):
        """Stop the approval agent server."""
        if self.process:
            print("🛑 Stopping Approval Agent...")
            self.process.terminate()
            try:
                self.process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait()
            self.process = None
            print("✅ Approval Agent stopped")

    async def test_agent_health(self):
        """Test agent health endpoint."""
        print("🏥 Testing agent health...")

        client = AuthenticatedTestClient(self.base_url)
        health_result = await client.test_health()

        assert health_result["success"], f"Health check failed: {health_result}"
        print("✅ Health check passed")

    async def test_agent_card(self):
        """Test agent card endpoint."""
        print("📋 Testing agent card...")

        client = AuthenticatedTestClient(self.base_url)
        card_result = await client.get_agent_card()

        assert card_result["success"], f"Agent card fetch failed: {card_result}"

        agent_card = card_result["agent_card"]
        assert agent_card["name"] == self.agent_name, f"Expected agent name {self.agent_name}, got {agent_card['name']}"
        assert "description" in agent_card, "Agent card should have description"

        print(f"✅ Agent card accessible: {agent_card['name']}")

    async def test_bearer_token_analysis(self):
        """Test bearer token analysis functionality."""
        print("🔑 Testing bearer token analysis...")

        # Create test token
        test_token = self.token_generator.create_test_token(
            user_id="test-user@example.com",
            agent_target=self.agent_name
        )

        client = AuthenticatedTestClient(self.base_url)

        # Send request with bearer token
        message = "Please verify my bearer token and confirm authentication context was received."
        result = await client.send_authenticated_message(
            message=message,
            bearer_token=test_token
        )

        assert result["success"], f"Bearer token analysis failed: {result}"

        # Verify authentication context was received
        response_text = result.get("message", "").lower()
        auth_indicators = [
            "authentication",
            "bearer token",
            "auth context",
            "approval",
            self.agent_name
        ]

        auth_present = any(indicator in response_text for indicator in auth_indicators)
        assert auth_present, f"Authentication context not detected in response: {response_text}"

        print("✅ Bearer token analysis working correctly")

    async def test_approval_tool(self):
        """Test approval tool functionality."""
        print("✋ Testing approval tool...")

        # Create test token
        test_token = self.token_generator.create_test_token(
            user_id="approver@example.com",
            agent_target=self.agent_name
        )

        client = AuthenticatedTestClient(self.base_url)

        # Test different approval workflows
        test_cases = [
            {
                "message": "Please request approval for document DOC-123 from manager@example.com",
                "expected_keywords": ["approval", "document", "doc-123", "request"]
            },
            {
                "message": "Please approve expense EXP-456 with comments",
                "expected_keywords": ["approve", "expense", "exp-456"]
            },
            {
                "message": "Please reject access request ACC-789 due to insufficient permissions",
                "expected_keywords": ["reject", "access", "acc-789"]
            },
            {
                "message": "Please escalate workflow WF-101 to senior management",
                "expected_keywords": ["escalate", "workflow", "wf-101", "senior"]
            }
        ]

        for i, test_case in enumerate(test_cases, 1):
            print(f"   Testing case {i}: {test_case['message'][:50]}...")

            result = await client.send_authenticated_message(
                message=test_case["message"],
                bearer_token=test_token
            )

            assert result["success"], f"Approval test case {i} failed: {result}"

            response_text = result.get("message", "").lower()
            for keyword in test_case["expected_keywords"]:
                assert keyword.lower() in response_text, \\
                    f"Expected keyword '{keyword}' not found in response: {response_text[:200]}"

            print(f"   ✅ Test case {i} passed")

        print("✅ Approval tool functionality verified")

    async def test_authentication_verification(self):
        """Test authentication context verification."""
        print("🔐 Testing authentication verification...")

        # Create test token with specific context
        test_token = self.token_generator.create_test_token(
            user_id="verification-test@example.com",
            agent_target=self.agent_name
        )

        client = AuthenticatedTestClient(self.base_url)

        # Request explicit authentication verification
        message = """
        Please use your approval tool and explicitly verify:
        1. That you received my bearer token
        2. That authentication context was properly forwarded
        3. Include the auth verification details in your response
        """

        result = await client.send_authenticated_message(
            message=message,
            bearer_token=test_token
        )

        assert result["success"], f"Authentication verification failed: {result}"

        # Use auth assertions helper
        AuthAssertions.assert_auth_context_forwarded(result, self.agent_name)
        AuthAssertions.assert_bearer_token_present(result)

        print("✅ Authentication verification successful")

    async def run_all_tests(self):
        """Run all tests for the approval agent."""
        print("🚀 Starting Approval Agent Tests")
        print("=" * 60)

        test_results = {}

        try:
            # Start the agent server
            server_started = await self.start_agent_server()
            assert server_started, "Failed to start agent server"

            # Give server additional time to fully initialize
            await asyncio.sleep(3)

            # Test 1: Health check
            try:
                await self.test_agent_health()
                test_results["health_test"] = "PASSED"
            except Exception as e:
                test_results["health_test"] = f"FAILED: {e}"
                logger.error(f"Health test failed: {e}")

            # Test 2: Agent card
            try:
                await self.test_agent_card()
                test_results["agent_card_test"] = "PASSED"
            except Exception as e:
                test_results["agent_card_test"] = f"FAILED: {e}"
                logger.error(f"Agent card test failed: {e}")

            # Test 3: Bearer token analysis
            try:
                await self.test_bearer_token_analysis()
                test_results["bearer_token_test"] = "PASSED"
            except Exception as e:
                test_results["bearer_token_test"] = f"FAILED: {e}"
                logger.error(f"Bearer token test failed: {e}")

            # Test 4: Approval tool
            try:
                await self.test_approval_tool()
                test_results["approval_test"] = "PASSED"
            except Exception as e:
                test_results["approval_test"] = f"FAILED: {e}"
                logger.error(f"Approval test failed: {e}")

            # Test 5: Authentication verification
            try:
                await self.test_authentication_verification()
                test_results["auth_verification_test"] = "PASSED"
            except Exception as e:
                test_results["auth_verification_test"] = f"FAILED: {e}"
                logger.error(f"Authentication verification test failed: {e}")

        finally:
            # Always stop the server
            await self.stop_agent_server()

        # Print results
        print("\\n" + "=" * 60)
        print("📊 APPROVAL AGENT TEST RESULTS")
        print("=" * 60)

        passed_tests = 0
        total_tests = len(test_results)

        for test_name, result in test_results.items():
            status = "✅ PASSED" if result == "PASSED" else f"❌ {result}"
            print(f"{test_name.replace('_', ' ').title():<35} {status}")
            if result == "PASSED":
                passed_tests += 1

        print("-" * 60)
        print(f"Summary: {passed_tests}/{total_tests} tests passed")

        if passed_tests == total_tests:
            print("🎉 All approval agent tests completed successfully!")
            return True
        else:
            print("⚠️  Some tests failed. Check logs for details.")
            return False


async def main():
    """Run all approval agent tests."""
    tester = ApprovalAgentTester()
    success = await tester.run_all_tests()

    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())