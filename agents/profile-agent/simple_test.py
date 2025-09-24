#!/usr/bin/env python3
"""
Simple test to check if the agent responds properly
"""

import httpx
import json

def test_basic_functionality():
    """Test basic agent functionality"""

    # Test 1: Health check
    print("🏥 Testing health endpoint...")
    try:
        response = httpx.get("http://localhost:8001/health", timeout=10.0)
        print(f"Health Status: {response.status_code}")
        if response.status_code == 200:
            print(f"Health Response: {response.json()}")
        else:
            print(f"Health Error: {response.text}")
    except Exception as e:
        print(f"Health Check Failed: {e}")

    print("\n" + "="*50)

    # Test 2: Agent Card
    print("📋 Testing agent card...")
    try:
        response = httpx.get("http://localhost:8001/.well-known/agent-card.json", timeout=10.0)
        print(f"Agent Card Status: {response.status_code}")
        if response.status_code == 200:
            card = response.json()
            print(f"Agent Name: {card.get('name')}")
            print(f"Agent Description: {card.get('description')}")
            print(f"Security Schemes: {list(card.get('securitySchemes', {}).keys())}")
        else:
            print(f"Agent Card Error: {response.text}")
    except Exception as e:
        print(f"Agent Card Failed: {e}")

    print("\n" + "="*50)

    # Test 3: Try message without auth (to see what error we get)
    print("💬 Testing message endpoint without auth...")
    payload = {
        "jsonrpc": "2.0",
        "id": "test-1",
        "method": "message/send",
        "params": {
            "message": {
                "role": "user",
                "parts": [{"type": "text", "text": "get my profile"}],
                "messageId": "msg-1"
            }
        }
    }

    try:
        response = httpx.post(
            "http://localhost:8001",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=10.0
        )
        print(f"Message Status: {response.status_code}")
        try:
            result = response.json()
            print(f"Message Response: {json.dumps(result, indent=2)}")
        except:
            print(f"Message Response (text): {response.text}")
    except Exception as e:
        print(f"Message Test Failed: {e}")

    print("\n" + "="*50)

    # Test 4: Auth status
    print("🔐 Testing auth status...")
    try:
        response = httpx.get(
            "http://localhost:8001/auth/status",
            params={"user_id": "test_user"},
            timeout=10.0
        )
        print(f"Auth Status Code: {response.status_code}")
        try:
            result = response.json()
            print(f"Auth Status: {json.dumps(result, indent=2)}")
        except:
            print(f"Auth Status (text): {response.text}")
    except Exception as e:
        print(f"Auth Status Failed: {e}")

if __name__ == "__main__":
    test_basic_functionality()