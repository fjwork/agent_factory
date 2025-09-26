#!/usr/bin/env python3
"""
OAuth Test Client for Agent Template

This script demonstrates the complete OAuth flow:
1. Initiate OAuth authentication
2. Complete the authentication
3. Send authenticated requests to test agent tools
"""

import httpx
import json
import asyncio
import time
from typing import Optional

class AgentTestClient:
    def __init__(self, base_url: str = "http://localhost:8001"):
        self.base_url = base_url
        self.session_id: Optional[str] = None

    async def initiate_oauth(self, user_id: str, provider: str = "google") -> dict:
        """Step 1: Initiate OAuth flow"""
        print(f"🔐 Initiating OAuth flow for user: {user_id}")

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/auth/initiate",
                json={
                    "user_id": user_id,
                    "provider": provider
                },
                timeout=30.0
            )

            if response.status_code == 200:
                auth_data = response.json()
                self.session_id = auth_data.get("session_id")
                return auth_data
            else:
                print(f"❌ OAuth initiation failed: {response.status_code}")
                print(response.text)
                return {}

    async def check_auth_status(self, user_id: str, provider: str = "google") -> dict:
        """Check authentication status"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/auth/status",
                params={
                    "user_id": user_id,
                    "provider": provider
                },
                timeout=30.0
            )

            if response.status_code == 200:
                return response.json()
            else:
                print(f"❌ Auth status check failed: {response.status_code}")
                return {}

    async def complete_oauth(self, authorization_code: str) -> dict:
        """Step 2: Complete OAuth flow (for authorization code flow)"""
        if not self.session_id:
            print("❌ No session ID available. Run initiate_oauth first.")
            return {}

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/auth/complete",
                json={
                    "session_id": self.session_id,
                    "authorization_code": authorization_code
                },
                timeout=30.0
            )

            if response.status_code == 200:
                return response.json()
            else:
                print(f"❌ OAuth completion failed: {response.status_code}")
                print(response.text)
                return {}

    async def send_authenticated_message(self, user_id: str, message: str) -> dict:
        """Step 3: Send authenticated message"""
        print(f"💬 Sending message: {message}")

        # Prepare A2A message payload
        payload = {
            "jsonrpc": "2.0",
            "id": "request-1",
            "user_id": user_id,  # Move user_id to root level for auth handler
            "method": "message/send",
            "params": {
                "message": {
                    "role": "user",
                    "parts": [
                        {
                            "type": "text",
                            "text": message
                        }
                    ],
                    "messageId": f"msg-{int(time.time())}"
                }
            }
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.base_url,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=30.0
            )

            print(f"📊 Response Status: {response.status_code}")

            try:
                return response.json()
            except:
                return {"error": "Invalid JSON response", "text": response.text}

async def main():
    """Main OAuth flow demonstration"""

    print("🚀 Profile Agent OAuth Test Client")
    print("=" * 50)

    client = ProfileAgentClient()
    user_id = "flammoglia@google.com"  # Use real user email

    # Step 1: Check current auth status
    print("\n📋 Step 1: Checking current authentication status...")
    auth_status = await client.check_auth_status(user_id)
    print(f"Auth Status: {json.dumps(auth_status, indent=2)}")

    if auth_status.get("authenticated"):
        print("✅ User is already authenticated!")

        # Skip to sending message
        print("\n💬 Step 3: Sending authenticated profile request...")
        result = await client.send_authenticated_message(user_id, "get my profile")
        print(f"Profile Response: {json.dumps(result, indent=2)}")

    else:
        print("🔑 User needs to authenticate...")

        # Step 2: Initiate OAuth
        print("\n🔐 Step 2: Initiating OAuth flow...")
        auth_data = await client.initiate_oauth(user_id)

        if auth_data:
            print(f"OAuth Initiation: {json.dumps(auth_data, indent=2)}")

            if auth_data.get("flow_type") == "device_flow":
                print(f"\n📱 Device Flow Instructions:")
                print(f"   1. Go to: {auth_data.get('verification_url')}")
                print(f"   2. Enter code: {auth_data.get('user_code')}")
                print(f"   3. Complete authorization in your browser")
                print(f"\n⏱️  Waiting for you to complete the OAuth flow...")

                # Wait for user to complete OAuth
                input("Press Enter after completing OAuth in your browser...")

                # Check if auth is now complete
                auth_status = await client.check_auth_status(user_id)
                if auth_status.get("authenticated"):
                    print("✅ Authentication successful!")

                    # Send authenticated message
                    print("\n💬 Sending authenticated profile request...")
                    result = await client.send_authenticated_message(user_id, "get my profile")
                    print(f"Profile Response: {json.dumps(result, indent=2)}")
                else:
                    print("❌ Authentication not completed. Please try again.")

            elif auth_data.get("flow_type") == "authorization_code":
                print(f"\n🔗 Authorization Code Flow:")
                print(f"   1. Go to: {auth_data.get('authorization_url')}")
                print(f"   2. Complete authorization")
                print(f"   3. Copy the authorization code")

                auth_code = input("\n📝 Enter the authorization code: ")

                if auth_code:
                    complete_result = await client.complete_oauth(auth_code)
                    print(f"OAuth Completion: {json.dumps(complete_result, indent=2)}")

                    if complete_result.get("status") == "completed":
                        print("✅ Authentication successful!")

                        # Send authenticated message
                        print("\n💬 Sending authenticated profile request...")
                        result = await client.send_authenticated_message(user_id, "get my profile")
                        print(f"Profile Response: {json.dumps(result, indent=2)}")
                    else:
                        print("❌ Authentication failed")
        else:
            print("❌ Failed to initiate OAuth flow")

if __name__ == "__main__":
    asyncio.run(main())