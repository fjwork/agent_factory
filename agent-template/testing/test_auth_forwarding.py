"""
End-to-end authentication forwarding test between root and remote agents

This script tests:
1. Bearer token forwarding from root agent to remote agents
2. OAuth context forwarding from root agent to remote agents
3. Authentication context preservation across A2A boundaries
4. Multi-agent delegation workflows with authentication
"""

import asyncio
import logging
import os
import sys
import subprocess
import time
from pathlib import Path
from typing import Dict, List, Optional

# Add src and testing to path
project_root = Path(__file__).parent.parent
src_dir = project_root / "src"
testing_dir = project_root / "testing"
sys.path.insert(0, str(src_dir))
sys.path.insert(0, str(testing_dir))

from utils.test_client import AuthenticatedTestClient
from utils.auth_test_utils import BearerTokenGenerator, OAuthContextGenerator, AuthFlowTester, AuthAssertions

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class AuthForwardingTester:
    """Comprehensive authentication forwarding test suite."""

    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.root_agent_url = "http://localhost:8001"
        self.remote_agents = {
            "data_analysis_agent": {
                "url": "http://localhost:8002",
                "port": 8002,
                "module_path": self.project_root / "testing" / "remote_agents" / "data_analysis_agent" / "src" / "agent.py"
            },
            "notification_agent": {
                "url": "http://localhost:8003",
                "port": 8003,
                "module_path": self.project_root / "testing" / "remote_agents" / "notification_agent" / "src" / "agent.py"
            },
            "approval_agent": {
                "url": "http://localhost:8004",
                "port": 8004,
                "module_path": self.project_root / "testing" / "remote_agents" / "approval_agent" / "src" / "agent.py"
            }
        }
        self.running_processes = {}
        self.token_generator = BearerTokenGenerator()
        self.oauth_generator = OAuthContextGenerator()

    async def start_all_agents(self) -> bool:
        """Start all remote agents."""
        print("🚀 Starting all remote agents for auth forwarding tests...")

        for agent_name, config in self.remote_agents.items():
            success = await self._start_agent(agent_name, config)
            if not success:
                print(f"❌ Failed to start {agent_name}")
                await self.stop_all_agents()
                return False

        # Wait for all agents to fully initialize
        print("⏳ Waiting for all agents to fully initialize...")
        await asyncio.sleep(5)

        # Verify all agents are healthy
        all_healthy = await self._verify_all_agents_healthy()
        if not all_healthy:
            await self.stop_all_agents()
            return False

        print("✅ All remote agents started and healthy")
        return True

    async def _start_agent(self, agent_name: str, config: Dict) -> bool:
        """Start a single agent."""
        print(f"   Starting {agent_name} on port {config['port']}...")

        try:
            # Set environment variables
            env = dict(os.environ)
            env[f"{agent_name.upper()}_PORT"] = str(config["port"])
            env[f"{agent_name.upper()}_HOST"] = "localhost"
            env["LOG_LEVEL"] = "INFO"

            # Start the agent process
            process = subprocess.Popen(
                [sys.executable, str(config["module_path"])],
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )

            self.running_processes[agent_name] = process

            # Wait for agent to start
            client = AuthenticatedTestClient(config["url"])
            started = await client.wait_for_agent_ready(max_retries=10, delay=2.0)

            if started:
                print(f"   ✅ {agent_name} started successfully")
                return True
            else:
                print(f"   ❌ {agent_name} failed to start")
                return False

        except Exception as e:
            logger.error(f"Failed to start {agent_name}: {e}")
            return False

    async def _verify_all_agents_healthy(self) -> bool:
        """Verify all agents are healthy."""
        for agent_name, config in self.remote_agents.items():
            client = AuthenticatedTestClient(config["url"])
            health_result = await client.test_health()

            if not health_result["success"]:
                print(f"❌ {agent_name} health check failed")
                return False

        return True

    async def stop_all_agents(self):
        """Stop all running agents."""
        print("🛑 Stopping all remote agents...")

        for agent_name, process in self.running_processes.items():
            if process:
                print(f"   Stopping {agent_name}...")
                process.terminate()
                try:
                    process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()

        self.running_processes.clear()
        print("✅ All remote agents stopped")

    async def test_bearer_token_forwarding(self, target_agent: str) -> Dict:
        """Test bearer token forwarding from root to specific remote agent."""
        print(f"🔑 Testing Bearer Token Forwarding to {target_agent}")
        print("-" * 50)

        # Generate test token
        test_token = self.token_generator.create_test_token(
            user_id="auth-test@example.com",
            agent_target=target_agent,
            scopes=["read", "write", "delegate"]
        )

        # Create test client for root agent
        root_client = AuthenticatedTestClient(self.root_agent_url)

        # Send request to root agent asking it to delegate to remote agent
        delegation_request = f"""
        Please delegate this authentication verification task to the {target_agent}:

        Task: Analyze my bearer token and confirm that authentication context was properly forwarded.

        Requirements:
        1. Verify you received my bearer token
        2. Extract and display the user ID from the token
        3. Confirm the authentication type (bearer)
        4. Show that the token was forwarded correctly via A2A protocol

        Please include detailed authentication verification information in your response.
        """

        try:
            result = await root_client.send_authenticated_message(
                message=delegation_request,
                bearer_token=test_token
            )

            # Verify the delegation succeeded
            assert result["success"], f"Delegation to {target_agent} failed: {result}"

            # Use auth assertions to verify forwarding
            AuthAssertions.assert_auth_context_forwarded(result, target_agent)
            AuthAssertions.assert_bearer_token_present(result)

            print(f"✅ Bearer token successfully forwarded to {target_agent}")
            return {
                "status": "SUCCESS",
                "agent": target_agent,
                "token_user": "auth-test@example.com",
                "result": result
            }

        except Exception as e:
            print(f"❌ Bearer token forwarding to {target_agent} failed: {e}")
            return {
                "status": "FAILED",
                "agent": target_agent,
                "error": str(e)
            }

    async def test_oauth_context_forwarding(self, target_agent: str, provider: str = "google") -> Dict:
        """Test OAuth context forwarding from root to remote agent."""
        print(f"🔐 Testing OAuth Context Forwarding to {target_agent} (provider: {provider})")
        print("-" * 60)

        # Create OAuth test flow
        auth_tester = AuthFlowTester(self.root_agent_url)

        # Generate OAuth context
        oauth_context = self.oauth_generator.create_oauth_context(
            provider=provider,
            user_id="oauth-test@example.com"
        )

        # Create root client
        root_client = AuthenticatedTestClient(self.root_agent_url)

        # Send delegation request with OAuth context
        delegation_request = f"""
        Please delegate this OAuth verification task to the {target_agent}:

        Task: Verify that my OAuth authentication context was properly forwarded.

        Requirements:
        1. Verify you received my OAuth context
        2. Extract and display the OAuth provider ({provider})
        3. Confirm the user information was preserved
        4. Show that OAuth context was forwarded correctly via A2A protocol

        Please include detailed OAuth context verification information in your response.
        """

        try:
            result = await root_client.send_authenticated_message(
                message=delegation_request,
                user_id="oauth-test@example.com",
                oauth_context=oauth_context
            )

            # Verify the delegation succeeded
            assert result["success"], f"OAuth delegation to {target_agent} failed: {result}"

            # Use auth assertions to verify OAuth forwarding
            AuthAssertions.assert_auth_context_forwarded(result, target_agent)
            AuthAssertions.assert_oauth_context_present(result, provider)

            print(f"✅ OAuth context successfully forwarded to {target_agent}")
            return {
                "status": "SUCCESS",
                "agent": target_agent,
                "provider": provider,
                "oauth_user": "oauth-test@example.com",
                "result": result
            }

        except Exception as e:
            print(f"❌ OAuth context forwarding to {target_agent} failed: {e}")
            return {
                "status": "FAILED",
                "agent": target_agent,
                "provider": provider,
                "error": str(e)
            }

    async def test_multi_agent_delegation_chain(self) -> Dict:
        """Test authentication forwarding in a multi-agent delegation chain."""
        print("🔗 Testing Multi-Agent Delegation Chain with Authentication")
        print("-" * 60)

        # Create test token
        test_token = self.token_generator.create_test_token(
            user_id="chain-test@example.com",
            agent_target="multi_agent_chain"
        )

        root_client = AuthenticatedTestClient(self.root_agent_url)

        # Complex multi-step workflow
        workflow_request = """
        Please execute this multi-step workflow with authentication forwarding:

        Step 1: Use the data_analysis_agent to analyze sample sales data
        Step 2: Use the notification_agent to send a summary notification
        Step 3: Use the approval_agent to request approval for the analysis report

        For each step, ensure that:
        1. My authentication context is properly forwarded
        2. The agent verifies it received the authentication
        3. The workflow continues to the next step

        Please coordinate this workflow and provide status updates for each step.
        """

        try:
            result = await root_client.send_authenticated_message(
                message=workflow_request,
                bearer_token=test_token
            )

            assert result["success"], f"Multi-agent workflow failed: {result}"

            # Check that multiple agents were involved
            response_text = result.get("message", "").lower()
            expected_agents = ["data_analysis", "notification", "approval"]

            agents_mentioned = sum(1 for agent in expected_agents if agent in response_text)
            assert agents_mentioned >= 2, f"Expected multiple agents in workflow, only found {agents_mentioned}"

            print("✅ Multi-agent delegation chain with authentication successful")
            return {
                "status": "SUCCESS",
                "workflow": "multi_agent_chain",
                "agents_involved": agents_mentioned,
                "result": result
            }

        except Exception as e:
            print(f"❌ Multi-agent delegation chain failed: {e}")
            return {
                "status": "FAILED",
                "workflow": "multi_agent_chain",
                "error": str(e)
            }

    async def run_comprehensive_auth_tests(self):
        """Run comprehensive authentication forwarding tests."""
        print("🚀 Starting Comprehensive Authentication Forwarding Tests")
        print("=" * 70)

        test_results = {}

        try:
            # Start all remote agents
            agents_started = await self.start_all_agents()
            if not agents_started:
                print("❌ Failed to start all agents. Aborting tests.")
                return False

            # Wait for root agent to be ready (should be started separately)
            print("⏳ Checking root agent availability...")
            root_client = AuthenticatedTestClient(self.root_agent_url)
            root_ready = await root_client.wait_for_agent_ready(max_retries=5, delay=2.0)

            if not root_ready:
                print("❌ Root agent not available. Please start the root agent first.")
                return False

            print("✅ Root agent is ready")

            # Test 1: Bearer token forwarding to each agent
            print("\\n" + "=" * 70)
            print("🔑 BEARER TOKEN FORWARDING TESTS")
            print("=" * 70)

            for agent_name in self.remote_agents.keys():
                test_key = f"bearer_token_{agent_name}"
                try:
                    result = await self.test_bearer_token_forwarding(agent_name)
                    test_results[test_key] = result
                    print()
                except Exception as e:
                    test_results[test_key] = {
                        "status": "FAILED",
                        "agent": agent_name,
                        "error": str(e)
                    }
                    logger.error(f"Bearer token test for {agent_name} failed: {e}")

            # Test 2: OAuth context forwarding to each agent
            print("\\n" + "=" * 70)
            print("🔐 OAUTH CONTEXT FORWARDING TESTS")
            print("=" * 70)

            for agent_name in self.remote_agents.keys():
                for provider in ["google", "github"]:
                    test_key = f"oauth_{provider}_{agent_name}"
                    try:
                        result = await self.test_oauth_context_forwarding(agent_name, provider)
                        test_results[test_key] = result
                        print()
                    except Exception as e:
                        test_results[test_key] = {
                            "status": "FAILED",
                            "agent": agent_name,
                            "provider": provider,
                            "error": str(e)
                        }
                        logger.error(f"OAuth test for {agent_name} with {provider} failed: {e}")

            # Test 3: Multi-agent delegation chain
            print("\\n" + "=" * 70)
            print("🔗 MULTI-AGENT DELEGATION CHAIN TEST")
            print("=" * 70)

            try:
                result = await self.test_multi_agent_delegation_chain()
                test_results["multi_agent_chain"] = result
            except Exception as e:
                test_results["multi_agent_chain"] = {
                    "status": "FAILED",
                    "error": str(e)
                }
                logger.error(f"Multi-agent chain test failed: {e}")

        finally:
            # Always stop all agents
            await self.stop_all_agents()

        # Print comprehensive results
        self._print_test_results(test_results)

        # Return success status
        success_count = sum(1 for result in test_results.values() if result.get("status") == "SUCCESS")
        total_count = len(test_results)

        return success_count == total_count

    def _print_test_results(self, test_results: Dict):
        """Print comprehensive test results."""
        print("\\n" + "=" * 70)
        print("📊 COMPREHENSIVE AUTHENTICATION FORWARDING TEST RESULTS")
        print("=" * 70)

        success_count = 0
        total_count = len(test_results)

        # Group results by category
        bearer_tests = {k: v for k, v in test_results.items() if k.startswith("bearer_token_")}
        oauth_tests = {k: v for k, v in test_results.items() if k.startswith("oauth_")}
        chain_tests = {k: v for k, v in test_results.items() if k.startswith("multi_agent_")}

        # Print bearer token results
        if bearer_tests:
            print("\\n🔑 Bearer Token Forwarding Results:")
            print("-" * 40)
            for test_name, result in bearer_tests.items():
                agent_name = test_name.replace("bearer_token_", "")
                status = "✅ SUCCESS" if result.get("status") == "SUCCESS" else f"❌ {result.get('status', 'FAILED')}"
                print(f"  {agent_name:<20} {status}")
                if result.get("status") == "SUCCESS":
                    success_count += 1

        # Print OAuth results
        if oauth_tests:
            print("\\n🔐 OAuth Context Forwarding Results:")
            print("-" * 40)
            for test_name, result in oauth_tests.items():
                parts = test_name.replace("oauth_", "").split("_", 1)
                provider = parts[0]
                agent_name = parts[1] if len(parts) > 1 else "unknown"
                status = "✅ SUCCESS" if result.get("status") == "SUCCESS" else f"❌ {result.get('status', 'FAILED')}"
                print(f"  {provider}/{agent_name:<15} {status}")
                if result.get("status") == "SUCCESS":
                    success_count += 1

        # Print chain results
        if chain_tests:
            print("\\n🔗 Multi-Agent Chain Results:")
            print("-" * 40)
            for test_name, result in chain_tests.items():
                status = "✅ SUCCESS" if result.get("status") == "SUCCESS" else f"❌ {result.get('status', 'FAILED')}"
                print(f"  {test_name:<20} {status}")
                if result.get("status") == "SUCCESS":
                    success_count += 1

        # Print summary
        print("\\n" + "=" * 70)
        print(f"📈 SUMMARY: {success_count}/{total_count} tests passed")

        if success_count == total_count:
            print("🎉 ALL AUTHENTICATION FORWARDING TESTS PASSED!")
        else:
            print(f"⚠️  {total_count - success_count} tests failed. Check details above.")

        print("=" * 70)


async def main():
    """Run all authentication forwarding tests."""
    tester = AuthForwardingTester()
    success = await tester.run_comprehensive_auth_tests()

    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())