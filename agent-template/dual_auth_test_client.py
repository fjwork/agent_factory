#!/usr/bin/env python3
"""
Dual Authentication Test Client

This client tests both bearer token and OAuth device flow authentication patterns.
It demonstrates the new dual authentication capability.

Usage:
    # Test bearer token (with environment variable control)
    BEARER_TOKEN_VALIDATION=valid python dual_auth_test_client.py --test-bearer

    # Test OAuth device flow (existing pattern)
    python dual_auth_test_client.py --test-oauth

    # Test both
    python dual_auth_test_client.py --test-both
"""

import asyncio
import aiohttp
import argparse
import json
import os
import sys
from typing import Dict, Any, Optional


class DualAuthTestClient:
    """Test client for dual authentication (Bearer token + OAuth device flow)."""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def test_health_check(self) -> Dict[str, Any]:
        """Test health endpoint and get authentication status."""
        print("🏥 Testing health check endpoint...")

        async with self.session.get(f"{self.base_url}/health") as response:
            if response.status == 200:
                data = await response.json()
                print(f"✅ Health check successful")
                print(f"   Agent: {data.get('agent')}")
                print(f"   Authentication: {data.get('authentication')}")
                return data
            else:
                print(f"❌ Health check failed: {response.status}")
                return {}

    async def test_dual_auth_status(self, bearer_token: Optional[str] = None) -> Dict[str, Any]:
        """Test dual authentication status endpoint."""
        print("🔍 Testing dual authentication status...")

        headers = {}
        if bearer_token:
            headers["Authorization"] = f"Bearer {bearer_token}"
            print(f"   Using bearer token: {bearer_token[:20]}...")

        async with self.session.get(f"{self.base_url}/auth/dual-status", headers=headers) as response:
            if response.status == 200:
                data = await response.json()
                print(f"✅ Dual auth status retrieved")
                self._print_auth_status(data)
                return data
            else:
                text = await response.text()
                print(f"❌ Dual auth status failed: {response.status}")
                print(f"   Response: {text}")
                return {}

    async def test_bearer_token_authentication(self, token: str = "test-bearer-token") -> Dict[str, Any]:
        """Test bearer token authentication with A2A request."""
        print(f"🔐 Testing bearer token authentication...")
        print(f"   Token: {token}")
        print(f"   Validation mode: {os.getenv('BEARER_TOKEN_VALIDATION', 'jwt')}")

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        # Create A2A message
        a2a_message = {
            "jsonrpc": "2.0",
            "id": "bearer-test-1",
            "method": "message/send",
            "params": {
                "message": {
                    "role": "user",
                    "content": [{"text": "Test message with bearer token authentication"}]
                },
                "context_id": "bearer-test-context"
            }
        }

        async with self.session.post(f"{self.base_url}/", headers=headers, json=a2a_message) as response:
            status = response.status
            data = await response.json()

            if status == 200:
                print(f"✅ Bearer token authentication successful")
                print(f"   Response ID: {data.get('id')}")
                if 'result' in data:
                    print(f"   Agent responded successfully")
                return data
            elif status == 401:
                print(f"🔒 Bearer token authentication failed (as expected if validation=invalid)")
                print(f"   Error: {data.get('error')}")
                print(f"   Supported methods: {data.get('supported_methods', [])}")
                return data
            else:
                print(f"❌ Unexpected response: {status}")
                print(f"   Data: {data}")
                return data

    async def test_oauth_device_flow(self, user_id: str = "test-oauth-user@example.com") -> Dict[str, Any]:
        """Test OAuth device flow authentication."""
        print(f"🔑 Testing OAuth device flow...")
        print(f"   User ID: {user_id}")

        # Step 1: Initiate OAuth flow
        print("   Step 1: Initiating OAuth flow...")
        init_data = {
            "user_id": user_id,
            "provider": "google"
        }

        async with self.session.post(f"{self.base_url}/auth/initiate", json=init_data) as response:
            if response.status != 200:
                print(f"❌ OAuth initiation failed: {response.status}")
                return {}

            auth_info = await response.json()
            print(f"✅ OAuth flow initiated")
            print(f"   Flow type: {auth_info.get('flow_type')}")
            print(f"   Verification URL: {auth_info.get('verification_url')}")
            print(f"   User code: {auth_info.get('user_code')}")

        # Step 2: Test A2A request with user context
        print("   Step 2: Testing A2A request with OAuth user context...")

        a2a_message = {
            "jsonrpc": "2.0",
            "id": "oauth-test-1",
            "method": "message/send",
            "params": {
                "message": {
                    "role": "user",
                    "content": [{"text": "Test message with OAuth device flow"}]
                },
                "context_id": "oauth-test-context"
            },
            "user_id": user_id  # Include user_id for OAuth context lookup
        }

        async with self.session.post(f"{self.base_url}/", json=a2a_message) as response:
            status = response.status
            data = await response.json()

            if status == 401:
                print(f"🔒 OAuth authentication required (expected - user needs to complete device flow)")
                print(f"   Error: {data.get('error')}")
                print(f"   Supported methods: {data.get('supported_methods', [])}")
                return data
            elif status == 200:
                print(f"✅ OAuth authentication successful (user had existing token)")
                return data
            else:
                print(f"❌ Unexpected response: {status}")
                print(f"   Data: {data}")
                return data

    async def test_a2a_without_auth(self) -> Dict[str, Any]:
        """Test A2A request without any authentication."""
        print("🚫 Testing A2A request without authentication...")

        a2a_message = {
            "jsonrpc": "2.0",
            "id": "no-auth-test-1",
            "method": "message/send",
            "params": {
                "message": {
                    "role": "user",
                    "content": [{"text": "Test message without authentication"}]
                },
                "context_id": "no-auth-test-context"
            }
        }

        async with self.session.post(f"{self.base_url}/", json=a2a_message) as response:
            status = response.status
            data = await response.json()

            if status == 401:
                print(f"🔒 Authentication required (expected)")
                print(f"   Error: {data.get('error')}")
                print(f"   Supported methods: {data.get('supported_methods', [])}")
                return data
            else:
                print(f"❌ Unexpected response: {status} (expected 401)")
                print(f"   Data: {data}")
                return data

    def _print_auth_status(self, status: Dict[str, Any]):
        """Print authentication status in a readable format."""
        print(f"   Dual authentication: {status.get('dual_authentication_enabled')}")
        print(f"   Supported methods: {status.get('supported_methods', [])}")
        print(f"   Bearer validation: {status.get('bearer_token_validation')}")

        current_auth = status.get('current_authentication', {})
        if current_auth.get('authenticated'):
            print(f"   Current user: {current_auth.get('user_id')} ({current_auth.get('auth_type')})")
        else:
            print(f"   Current user: Not authenticated")

        env_testing = status.get('environment_testing', {})
        if env_testing:
            print(f"   Test modes - Valid: {env_testing.get('bearer_valid_mode')}, Invalid: {env_testing.get('bearer_invalid_mode')}")

    async def run_full_test_suite(self):
        """Run complete test suite for dual authentication."""
        print("🚀 Starting Dual Authentication Test Suite")
        print("=" * 60)

        # Test 1: Health check
        await self.test_health_check()
        print()

        # Test 2: Dual auth status (no auth)
        await self.test_dual_auth_status()
        print()

        # Test 3: No authentication
        await self.test_a2a_without_auth()
        print()

        # Test 4: Bearer token authentication
        bearer_token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJ0ZXN0LWJlYXJlci11c2VyQGV4YW1wbGUuY29tIiwiZW1haWwiOiJ0ZXN0LWJlYXJlci11c2VyQGV4YW1wbGUuY29tIiwibmFtZSI6IlRlc3QgQmVhcmVyIFVzZXIiLCJpYXQiOjE3MDAwMDAwMDAsImV4cCI6OTk5OTk5OTk5OX0.example"
        await self.test_bearer_token_authentication(bearer_token)
        print()

        # Test 5: Dual auth status (with bearer token)
        await self.test_dual_auth_status(bearer_token)
        print()

        # Test 6: OAuth device flow
        await self.test_oauth_device_flow()
        print()

        print("✅ Test suite completed!")


async def main():
    parser = argparse.ArgumentParser(description="Test dual authentication functionality")
    parser.add_argument("--url", default="http://localhost:8000", help="Agent server URL")
    parser.add_argument("--test-bearer", action="store_true", help="Test bearer token authentication")
    parser.add_argument("--test-oauth", action="store_true", help="Test OAuth device flow")
    parser.add_argument("--test-both", action="store_true", help="Test both authentication methods")
    parser.add_argument("--bearer-token", default=None, help="Bearer token to test with")

    args = parser.parse_args()

    # Check environment variable settings
    bearer_validation = os.getenv("BEARER_TOKEN_VALIDATION", "jwt")
    print(f"🔧 Environment: BEARER_TOKEN_VALIDATION={bearer_validation}")

    if bearer_validation == "valid":
        print("   📝 Bearer tokens will always validate successfully (testing mode)")
    elif bearer_validation == "invalid":
        print("   📝 Bearer tokens will always fail validation (testing mode)")
    else:
        print("   📝 Bearer tokens will be validated as JWTs (production mode)")

    print()

    async with DualAuthTestClient(args.url) as client:
        try:
            if args.test_both or (not args.test_bearer and not args.test_oauth):
                await client.run_full_test_suite()
            else:
                # Run individual tests
                await client.test_health_check()
                print()

                if args.test_bearer:
                    token = args.bearer_token or "test-bearer-token"
                    await client.test_bearer_token_authentication(token)
                    print()

                if args.test_oauth:
                    await client.test_oauth_device_flow()
                    print()

        except aiohttp.ClientConnectorError:
            print(f"❌ Failed to connect to {args.url}")
            print("   Make sure the agent server is running:")
            print("   cd src && python agent.py")
            sys.exit(1)
        except Exception as e:
            print(f"❌ Test failed with error: {e}")
            sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())