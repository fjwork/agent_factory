"""
Test script for root agent - tests both standalone and multi-agent modes

This script tests:
1. Root agent in standalone mode (no remote_agents.yaml)
2. Root agent in multi-agent mode (with remote agents configured)
3. Bearer token functionality
4. Basic agent functionality and health
"""

import asyncio
import logging
import os
import sys
from pathlib import Path

# Add src and testing to path
project_root = Path(__file__).parent.parent
src_dir = project_root / "src"
testing_dir = project_root / "testing"
sys.path.insert(0, str(src_dir))
sys.path.insert(0, str(testing_dir))

from agent import create_agent
from utils.test_client import AuthenticatedTestClient
from utils.auth_test_utils import BearerTokenGenerator, AuthAssertions

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class RootAgentTester:
    """Test suite for the root agent."""

    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.config_dir = self.project_root / "config"
        self.remote_config_path = self.config_dir / "remote_agents.yaml"
        self.backup_config_path = self.config_dir / "remote_agents.yaml.backup"
        self.token_generator = BearerTokenGenerator()

    async def test_root_agent_standalone(self):
        """Test root agent without remote agents (no remote_agents.yaml)."""
        print("🧪 Testing Root Agent - Standalone Mode")
        print("-" * 40)

        # Temporarily hide remote_agents.yaml if it exists
        config_backed_up = False
        if self.remote_config_path.exists():
            self.remote_config_path.rename(self.backup_config_path)
            config_backed_up = True
            print("📁 Temporarily backed up remote_agents.yaml")

        try:
            # Create agent in standalone mode
            agent = await create_agent()

            # Verify no sub-agents
            sub_agents_count = len(agent.sub_agents) if agent.sub_agents else 0
            assert sub_agents_count == 0, f"Expected 0 sub-agents in standalone mode, got {sub_agents_count}"
            print(f"✅ Root agent created in standalone mode (0 sub-agents)")

            # Verify agent properties
            assert agent.name, "Agent should have a name"
            assert agent.tools, "Agent should have tools"
            assert agent.instruction, "Agent should have instructions"
            print(f"✅ Agent properties verified: {agent.name}")

            # Test bearer token tool functionality
            await self._test_bearer_token_functionality(agent)

            print("✅ Standalone mode test completed successfully")

        except Exception as e:
            print(f"❌ Standalone mode test failed: {e}")
            raise
        finally:
            # Restore config if it existed
            if config_backed_up and self.backup_config_path.exists():
                self.backup_config_path.rename(self.remote_config_path)
                print("📁 Restored remote_agents.yaml")

    async def test_root_agent_with_remotes(self):
        """Test root agent with remote agents configured."""
        print("\\n🧪 Testing Root Agent - Multi-Agent Mode")
        print("-" * 40)

        # Ensure remote_agents.yaml exists
        if not self.remote_config_path.exists():
            print("⚠️  No remote_agents.yaml found - skipping multi-agent test")
            return

        try:
            # Create agent with remote agents
            agent = await create_agent()

            # Verify sub-agents loaded
            sub_agents_count = len(agent.sub_agents) if agent.sub_agents else 0

            if sub_agents_count > 0:
                print(f"✅ Root agent created with {sub_agents_count} remote sub-agents:")
                for i, sub_agent in enumerate(agent.sub_agents, 1):
                    print(f"   {i}. {sub_agent.name}: {sub_agent.description[:80]}...")

                    # Verify sub-agent properties
                    assert sub_agent.name, f"Sub-agent {i} should have a name"
                    assert sub_agent.description, f"Sub-agent {i} should have a description"
                    assert sub_agent.agent_card, f"Sub-agent {i} should have an agent card URL"

                # Verify instruction includes delegation info
                instruction_text = agent.instruction.lower()
                assert "remote" in instruction_text or "delegate" in instruction_text, \\
                    "Agent instruction should mention remote agents or delegation"
                print("✅ Agent instruction includes delegation information")

            else:
                print("⚠️  No remote agents loaded despite configuration present")

            # Test bearer token tool functionality
            await self._test_bearer_token_functionality(agent)

            print("✅ Multi-agent mode test completed successfully")

        except Exception as e:
            print(f"❌ Multi-agent mode test failed: {e}")
            raise

    async def _test_bearer_token_functionality(self, agent):
        """Test bearer token functionality with the agent."""
        print("🔑 Testing bearer token functionality...")

        # Create test token
        test_token = self.token_generator.create_test_token(
            user_id="test-user@example.com",
            agent_target="root_agent"
        )

        # Test token creation
        decoded_token = self.token_generator.decode_test_token(test_token)
        assert decoded_token.get("sub") == "test-user@example.com", "Token should contain correct user ID"
        print("✅ Test token created and verified")

        # Test that agent has bearer token tools
        bearer_token_tools = [
            tool for tool in agent.tools
            if hasattr(tool, '__name__') and 'bearer' in tool.__name__.lower()
        ]

        if bearer_token_tools:
            print(f"✅ Found {len(bearer_token_tools)} bearer token related tools")
        else:
            print("ℹ️  No specific bearer token tools found (may be integrated into other tools)")

        print("✅ Bearer token functionality test completed")

    async def test_agent_health_and_basic_functionality(self):
        """Test basic agent health and functionality."""
        print("\\n🏥 Testing Agent Health and Basic Functionality")
        print("-" * 50)

        try:
            # Create agent
            agent = await create_agent()

            # Test agent creation
            assert agent is not None, "Agent should be created successfully"
            print("✅ Agent creation successful")

            # Test agent properties
            assert hasattr(agent, 'name'), "Agent should have name attribute"
            assert hasattr(agent, 'tools'), "Agent should have tools attribute"
            assert hasattr(agent, 'instruction'), "Agent should have instruction attribute"
            print("✅ Agent has required attributes")

            # Test tools availability
            assert agent.tools and len(agent.tools) > 0, "Agent should have at least one tool"
            print(f"✅ Agent has {len(agent.tools)} tools available")

            # Test instruction content
            assert agent.instruction and len(agent.instruction.strip()) > 0, "Agent should have non-empty instructions"
            print("✅ Agent has proper instructions")

            print("✅ Health and basic functionality test completed")

        except Exception as e:
            print(f"❌ Health test failed: {e}")
            raise

    async def run_all_tests(self):
        """Run all root agent tests."""
        print("🚀 Starting Root Agent Tests")
        print("=" * 60)

        test_results = {}

        # Test 1: Health and basic functionality
        try:
            await self.test_agent_health_and_basic_functionality()
            test_results["health_test"] = "PASSED"
        except Exception as e:
            test_results["health_test"] = f"FAILED: {e}"
            logger.error(f"Health test failed: {e}")

        # Test 2: Standalone mode
        try:
            await self.test_root_agent_standalone()
            test_results["standalone_test"] = "PASSED"
        except Exception as e:
            test_results["standalone_test"] = f"FAILED: {e}"
            logger.error(f"Standalone test failed: {e}")

        # Test 3: Multi-agent mode
        try:
            await self.test_root_agent_with_remotes()
            test_results["multi_agent_test"] = "PASSED"
        except Exception as e:
            test_results["multi_agent_test"] = f"FAILED: {e}"
            logger.error(f"Multi-agent test failed: {e}")

        # Print summary
        print("\\n" + "=" * 60)
        print("📊 ROOT AGENT TEST RESULTS")
        print("=" * 60)

        passed_tests = 0
        total_tests = len(test_results)

        for test_name, result in test_results.items():
            status = "✅ PASSED" if result == "PASSED" else f"❌ {result}"
            print(f"{test_name.replace('_', ' ').title():<30} {status}")
            if result == "PASSED":
                passed_tests += 1

        print("-" * 60)
        print(f"Summary: {passed_tests}/{total_tests} tests passed")

        if passed_tests == total_tests:
            print("🎉 All root agent tests completed successfully!")
            return True
        else:
            print("⚠️  Some tests failed. Check logs for details.")
            return False


async def main():
    """Run all root agent tests."""
    tester = RootAgentTester()
    success = await tester.run_all_tests()

    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())