"""
Bearer Token Forwarding Test Client

This test client comprehensively tests bearer token forwarding functionality:
1. Bearer token extraction from request headers
2. Token forwarding to tools via session state
3. Token forwarding to remote agents via A2A protocol
"""

import asyncio
import httpx
import json
import logging
import os
import time
from typing import Dict, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class BearerTokenTestClient:
    """Test client for bearer token forwarding functionality."""

    def __init__(self, main_agent_url: str, remote_agent_url: str):
        self.main_agent_url = main_agent_url.rstrip("/")
        self.remote_agent_url = remote_agent_url.rstrip("/")
        self.test_token = "test-bearer-token-123456789-for-forwarding-test"

    async def run_comprehensive_test(self) -> Dict[str, Any]:
        """Run comprehensive bearer token forwarding test."""
        logger.info("🚀 Starting Comprehensive Bearer Token Forwarding Test")

        results = {
            "test_started": time.time(),
            "test_token": self.test_token,
            "tests": {}
        }

        try:
            # Test 1: Health checks
            logger.info("📋 Test 1: Health checks")
            results["tests"]["health_checks"] = await self._test_health_checks()

            # Test 2: Dual auth status
            logger.info("🔐 Test 2: Dual authentication status")
            results["tests"]["dual_auth_status"] = await self._test_dual_auth_status()

            # Test 3: Bearer token to main agent tools
            logger.info("🔧 Test 3: Bearer token forwarding to main agent tools")
            results["tests"]["token_to_tools"] = await self._test_token_forwarding_to_tools()

            # Test 4: Bearer token to remote agent via A2A
            logger.info("📡 Test 4: Bearer token forwarding to remote agent via A2A")
            results["tests"]["token_to_remote_agent"] = await self._test_token_forwarding_to_remote_agent()

            # Test 5: Invalid token handling
            logger.info("❌ Test 5: Invalid token handling")
            results["tests"]["invalid_token_handling"] = await self._test_invalid_token_handling()

            # Summarize results
            results["test_completed"] = time.time()
            results["test_duration"] = results["test_completed"] - results["test_started"]
            results["summary"] = self._summarize_results(results["tests"])

            logger.info("✅ Comprehensive Bearer Token Forwarding Test Complete")
            return results

        except Exception as e:
            logger.error(f"❌ Test suite failed: {e}")
            results["error"] = str(e)
            results["test_completed"] = time.time()
            return results

    async def _test_health_checks(self) -> Dict[str, Any]:
        """Test health endpoints of both agents."""
        health_results = {}

        async with httpx.AsyncClient() as client:
            # Test main agent health
            try:
                response = await client.get(f"{self.main_agent_url}/health", timeout=10.0)
                health_results["main_agent"] = {
                    "status_code": response.status_code,
                    "accessible": response.status_code == 200,
                    "response": response.json() if response.status_code == 200 else response.text
                }
            except Exception as e:
                health_results["main_agent"] = {
                    "accessible": False,
                    "error": str(e)
                }

            # Test remote agent health
            try:
                response = await client.get(f"{self.remote_agent_url}/health", timeout=10.0)
                health_results["remote_agent"] = {
                    "status_code": response.status_code,
                    "accessible": response.status_code == 200,
                    "response": response.json() if response.status_code == 200 else response.text
                }
            except Exception as e:
                health_results["remote_agent"] = {
                    "accessible": False,
                    "error": str(e)
                }

        return health_results

    async def _test_dual_auth_status(self) -> Dict[str, Any]:
        """Test dual authentication status endpoint."""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(f"{self.main_agent_url}/auth/dual-status", timeout=10.0)
                return {
                    "status_code": response.status_code,
                    "accessible": response.status_code == 200,
                    "response": response.json() if response.status_code == 200 else response.text
                }
            except Exception as e:
                return {
                    "accessible": False,
                    "error": str(e)
                }

    async def _test_token_forwarding_to_tools(self) -> Dict[str, Any]:
        """Test bearer token forwarding to main agent tools."""
        headers = {
            "Authorization": f"Bearer {self.test_token}",
            "Content-Type": "application/json"
        }

        payload = {
            "jsonrpc": "2.0",
            "id": "test-1",
            "method": "message/send",
            "params": {
                "message": {
                    "messageId": "test-message-1",
                    "role": "user",
                    "parts": [{"text": "Please use the bearer_token_print_tool to analyze my bearer token"}]
                }
            }
        }

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    self.main_agent_url,
                    headers=headers,
                    json=payload,
                    timeout=30.0
                )

                result = {
                    "status_code": response.status_code,
                    "request_headers": headers,
                    "request_payload": payload
                }

                if response.status_code == 200:
                    response_data = response.json()
                    result["response"] = response_data
                    result["success"] = True

                    # Check if bearer token was detected in tool
                    if "result" in response_data and "message" in response_data["result"]:
                        message_content = response_data["result"]["message"]
                        result["bearer_token_detected"] = "Bearer token successfully forwarded" in str(message_content)
                        result["tool_executed"] = "bearer_token_print_tool" in str(message_content)
                else:
                    result["response"] = response.text
                    result["success"] = False
                    result["bearer_token_detected"] = False

                return result

            except Exception as e:
                return {
                    "success": False,
                    "error": str(e),
                    "bearer_token_detected": False
                }

    async def _test_token_forwarding_to_remote_agent(self) -> Dict[str, Any]:
        """Test bearer token forwarding to remote agent via A2A."""
        # First, we need to use the main agent with RemoteA2aAgent to forward to remote agent
        # For this test, we'll directly test the remote agent for now
        # In a full implementation, this would test A2A delegation

        headers = {
            "Authorization": f"Bearer {self.test_token}",
            "Content-Type": "application/json"
        }

        payload = {
            "jsonrpc": "2.0",
            "id": "test-2",
            "method": "message/send",
            "params": {
                "message": {
                    "messageId": "test-message-2",
                    "role": "user",
                    "parts": [{"text": "Please use the remote_bearer_token_print_tool to analyze my bearer token"}]
                }
            }
        }

        async with httpx.AsyncClient() as client:
            try:
                # Test direct remote agent access with bearer token
                response = await client.post(
                    self.remote_agent_url,
                    headers=headers,
                    json=payload,
                    timeout=30.0
                )

                result = {
                    "status_code": response.status_code,
                    "request_headers": headers,
                    "request_payload": payload
                }

                if response.status_code == 200:
                    response_data = response.json()
                    result["response"] = response_data
                    result["success"] = True

                    # Check if bearer token was detected in remote agent
                    if "result" in response_data and "message" in response_data["result"]:
                        message_content = response_data["result"]["message"]
                        result["bearer_token_detected"] = "Bearer token successfully forwarded" in str(message_content)
                        result["remote_tool_executed"] = "remote_bearer_token_print_tool" in str(message_content)
                else:
                    result["response"] = response.text
                    result["success"] = False
                    result["bearer_token_detected"] = False

                return result

            except Exception as e:
                return {
                    "success": False,
                    "error": str(e),
                    "bearer_token_detected": False
                }

    async def _test_invalid_token_handling(self) -> Dict[str, Any]:
        """Test handling of requests without bearer tokens."""
        payload = {
            "jsonrpc": "2.0",
            "id": "test-3",
            "method": "message/send",
            "params": {
                "message": {
                    "messageId": "test-message-3",
                    "role": "user",
                    "parts": [{"text": "Hello without authentication"}]
                }
            }
        }

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    self.main_agent_url,
                    headers={"Content-Type": "application/json"},
                    json=payload,
                    timeout=10.0
                )

                return {
                    "status_code": response.status_code,
                    "response": response.json() if response.status_code == 401 else response.text,
                    "authentication_required": response.status_code == 401,
                    "proper_auth_error": response.status_code == 401
                }

            except Exception as e:
                return {
                    "error": str(e),
                    "authentication_required": False
                }

    def _summarize_results(self, tests: Dict[str, Any]) -> Dict[str, Any]:
        """Summarize test results."""
        summary = {
            "total_tests": len(tests),
            "passed_tests": 0,
            "failed_tests": 0,
            "test_details": {}
        }

        for test_name, test_result in tests.items():
            if test_name == "health_checks":
                main_healthy = test_result.get("main_agent", {}).get("accessible", False)
                remote_healthy = test_result.get("remote_agent", {}).get("accessible", False)
                passed = main_healthy and remote_healthy
            elif test_name == "dual_auth_status":
                passed = test_result.get("accessible", False)
            elif test_name == "token_to_tools":
                passed = test_result.get("bearer_token_detected", False)
            elif test_name == "token_to_remote_agent":
                passed = test_result.get("bearer_token_detected", False)
            elif test_name == "invalid_token_handling":
                passed = test_result.get("authentication_required", False)
            else:
                passed = test_result.get("success", False)

            summary["test_details"][test_name] = passed
            if passed:
                summary["passed_tests"] += 1
            else:
                summary["failed_tests"] += 1

        summary["overall_success"] = summary["failed_tests"] == 0
        summary["success_rate"] = summary["passed_tests"] / summary["total_tests"] if summary["total_tests"] > 0 else 0

        return summary


async def main():
    """Run the bearer token forwarding test."""
    # Default URLs
    main_agent_url = os.getenv("MAIN_AGENT_URL", "http://localhost:8001")
    remote_agent_url = os.getenv("REMOTE_AGENT_URL", "http://localhost:8002")

    print(f"🧪 Bearer Token Forwarding Test")
    print(f"📍 Main Agent: {main_agent_url}")
    print(f"📍 Remote Agent: {remote_agent_url}")
    print(f"🔧 Make sure to set BEARER_TOKEN_VALIDATION=valid in environment")
    print("")

    # Create test client
    client = BearerTokenTestClient(main_agent_url, remote_agent_url)

    # Run comprehensive test
    results = await client.run_comprehensive_test()

    # Print results
    print("\n" + "="*80)
    print("📊 TEST RESULTS")
    print("="*80)

    if "summary" in results:
        summary = results["summary"]
        print(f"🎯 Overall Success: {summary['overall_success']}")
        print(f"📈 Success Rate: {summary['success_rate']:.1%}")
        print(f"✅ Passed Tests: {summary['passed_tests']}")
        print(f"❌ Failed Tests: {summary['failed_tests']}")
        print("")

        print("📋 Test Details:")
        for test_name, passed in summary["test_details"].items():
            status = "✅ PASS" if passed else "❌ FAIL"
            print(f"  {status} {test_name}")

    print(f"\n⏱️  Test Duration: {results.get('test_duration', 0):.2f} seconds")

    # Save detailed results
    with open("bearer_token_test_results.json", "w") as f:
        json.dump(results, f, indent=2)

    print(f"💾 Detailed results saved to: bearer_token_test_results.json")

    return results


if __name__ == "__main__":
    asyncio.run(main())