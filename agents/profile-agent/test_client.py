#!/usr/bin/env python3
"""
Simple test client for the Profile Agent
"""

import httpx
import json
import uuid

def test_profile_agent():
    """Test the profile agent with a simple message."""

    # Server URL
    url = "http://localhost:8000"

    # Test message
    payload = {
        "jsonrpc": "2.0",
        "id": str(uuid.uuid4()),
        "method": "message/send",
        "params": {
            "user_id": "test_user_123",
            "message": {
                "role": "user",
                "parts": [
                    {
                        "type": "text",
                        "text": "get my profile"
                    }
                ],
                "messageId": str(uuid.uuid4())
            }
        }
    }

    print("🚀 Testing Profile Agent...")
    print(f"📡 Sending to: {url}")
    print(f"💬 Message: get my profile")
    print()

    try:
        with httpx.Client() as client:
            response = client.post(
                url,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=30.0
            )

            print(f"📊 Status Code: {response.status_code}")
            print(f"📝 Response:")

            try:
                response_data = response.json()
                print(json.dumps(response_data, indent=2))
            except:
                print(response.text)

    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_profile_agent()