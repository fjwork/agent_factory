#!/usr/bin/env python3
"""
Quick Test for Authentication Flow Agents

This script provides a quick verification that the agents are working correctly.
"""

import asyncio
import httpx
import json
import sys


async def quick_test():
    """Run a quick test of the authentication flow."""
    print("🔍 Quick Authentication Flow Test")
    print("=" * 50)

    # Test endpoints
    orchestrator_url = "http://localhost:8001"
    remote_url = "http://localhost:8002"

    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            # Test 1: Health checks
            print("1. Testing health endpoints...")

            try:
                response = await client.get(f"{orchestrator_url}/health")
                if response.status_code == 200:
                    print("   ✅ Orchestrator (8001) is healthy")
                else:
                    print(f"   ❌ Orchestrator health failed: {response.status_code}")
                    return False
            except Exception as e:
                print(f"   ❌ Cannot connect to orchestrator: {e}")
                return False

            try:
                response = await client.get(f"{remote_url}/health")
                if response.status_code == 200:
                    print("   ✅ Remote agent (8002) is healthy")
                else:
                    print(f"   ❌ Remote health failed: {response.status_code}")
                    return False
            except Exception as e:
                print(f"   ❌ Cannot connect to remote agent: {e}")
                return False

            # Test 2: Agent cards
            print("2. Testing agent cards...")

            try:
                response = await client.get(f"{orchestrator_url}/.well-known/agent-card.json")
                if response.status_code == 200:
                    card = response.json()
                    print(f"   ✅ Orchestrator card: {card.get('name', 'Unknown')}")
                else:
                    print(f"   ❌ Orchestrator card failed: {response.status_code}")
            except Exception as e:
                print(f"   ⚠️ Orchestrator card error: {e}")

            try:
                response = await client.get(f"{remote_url}/.well-known/agent-card.json")
                if response.status_code == 200:
                    card = response.json()
                    print(f"   ✅ Remote card: {card.get('name', 'Unknown')}")
                else:
                    print(f"   ❌ Remote card failed: {response.status_code}")
            except Exception as e:
                print(f"   ⚠️ Remote card error: {e}")

            # Test 3: Simple auth test
            print("3. Testing authentication...")

            test_request = {
                "jsonrpc": "2.0",
                "id": "quick-test",
                "method": "message/send",
                "params": {
                    "message": {
                        "role": "user",
                        "content": [{"text": "Quick authentication test"}]
                    }
                }
            }

            headers = {
                "Authorization": "Bearer quick-test-token",
                "Content-Type": "application/json"
            }

            try:
                response = await client.post(
                    f"{orchestrator_url}/",
                    json=test_request,
                    headers=headers
                )

                if response.status_code == 200:
                    result = response.json()
                    print("   ✅ Authentication test successful")

                    # Try to extract some useful info from response
                    if "result" in result:
                        task = result["result"]
                        if "artifacts" in task:
                            print(f"   📝 Response artifacts: {len(task['artifacts'])} items")
                        if "status" in task:
                            print(f"   📊 Task status: {task['status'].get('state', 'unknown')}")
                else:
                    print(f"   ❌ Auth test failed: {response.status_code}")
                    print(f"   Response: {response.text}")
                    return False

            except Exception as e:
                print(f"   ❌ Auth test error: {e}")
                return False

            print("=" * 50)
            print("🎉 Quick test completed successfully!")
            print("")
            print("💡 Next steps:")
            print("   - Run full test suite: python authenticated-flow-agent/test_auth_flow.py")
            print("   - Test manually with curl commands (see README.md)")
            print("   - Try different authentication methods")
            return True

        except Exception as e:
            print(f"❌ Quick test failed: {e}")
            return False


async def main():
    """Main function."""
    success = await quick_test()
    if not success:
        print("\n❌ Quick test failed. Check that both agents are running:")
        print("   ./start_agents.sh")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())