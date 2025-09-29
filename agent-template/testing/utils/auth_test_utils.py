"""
Authentication testing utilities for bearer token and OAuth testing
"""

import json
import time
import base64
import uuid
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class BearerTokenGenerator:
    """Generator for test bearer tokens with various configurations."""

    def __init__(self):
        self.secret_key = "test-secret-key-for-bearer-tokens"

    def create_test_token(
        self,
        user_id: str = "test-user@example.com",
        agent_target: str = "data_analysis_agent",
        scopes: list = None,
        expires_in: int = 3600
    ) -> str:
        """Create a test bearer token with specified parameters."""

        if scopes is None:
            scopes = ["read", "write", "delegate"]

        # Create token payload
        now = datetime.utcnow()
        payload = {
            "sub": user_id,
            "iss": "agent-template-test",
            "aud": agent_target,
            "iat": int(now.timestamp()),
            "exp": int((now + timedelta(seconds=expires_in)).timestamp()),
            "scopes": scopes,
            "token_type": "bearer",
            "test_context": {
                "generated_for": agent_target,
                "test_run_id": str(uuid.uuid4()),
                "purpose": "authentication_forwarding_test"
            }
        }

        # Simple base64 encoding for test purposes (not production JWT)
        token_data = json.dumps(payload)
        encoded_token = base64.b64encode(token_data.encode()).decode()

        return f"test.{encoded_token}.signature"

    def decode_test_token(self, token: str) -> Dict[str, Any]:
        """Decode a test bearer token."""
        try:
            # Remove 'test.' prefix and '.signature' suffix
            if token.startswith("test.") and token.endswith(".signature"):
                encoded_data = token[5:-10]  # Remove prefix and suffix
                decoded_data = base64.b64decode(encoded_data).decode()
                return json.loads(decoded_data)
            else:
                raise ValueError("Invalid test token format")
        except Exception as e:
            logger.error(f"Failed to decode test token: {e}")
            return {}

    def create_expired_token(self, user_id: str = "test-user@example.com") -> str:
        """Create an expired test token."""
        return self.create_test_token(user_id, expires_in=-3600)  # Expired 1 hour ago

    def create_invalid_token(self) -> str:
        """Create an intentionally invalid token for negative testing."""
        return "invalid.token.format"


class OAuthContextGenerator:
    """Generator for test OAuth contexts."""

    def __init__(self):
        self.providers = {
            "google": {
                "client_id": "test-google-client-id",
                "issuer": "https://accounts.google.com",
                "user_info_endpoint": "https://www.googleapis.com/oauth2/v2/userinfo"
            },
            "github": {
                "client_id": "test-github-client-id",
                "issuer": "https://github.com",
                "user_info_endpoint": "https://api.github.com/user"
            }
        }

    def create_oauth_context(
        self,
        provider: str = "google",
        user_id: str = "test-user@example.com",
        access_token: str = None
    ) -> Dict[str, Any]:
        """Create a test OAuth context."""

        if provider not in self.providers:
            raise ValueError(f"Unsupported provider: {provider}")

        if access_token is None:
            access_token = f"oauth2_{provider}_access_token_{uuid.uuid4().hex[:16]}"

        return {
            "provider": provider,
            "client_id": self.providers[provider]["client_id"],
            "access_token": access_token,
            "token_type": "Bearer",
            "scope": "openid email profile",
            "expires_at": int((datetime.utcnow() + timedelta(hours=1)).timestamp()),
            "user_info": {
                "sub": user_id,
                "email": user_id,
                "name": f"Test User ({user_id})",
                "picture": f"https://example.com/avatar/{user_id}",
                "provider": provider
            },
            "issued_at": int(datetime.utcnow().timestamp()),
            "test_context": {
                "generated_for_testing": True,
                "test_run_id": str(uuid.uuid4())
            }
        }


class AuthFlowTester:
    """Helper class for testing complete authentication flows."""

    def __init__(self, agent_base_url: str):
        self.agent_base_url = agent_base_url
        self.token_generator = BearerTokenGenerator()
        self.oauth_generator = OAuthContextGenerator()
        self.active_sessions = {}

    async def initiate_oauth_flow(self, user_id: str, provider: str = "google") -> Dict[str, Any]:
        """Simulate initiating an OAuth flow."""
        session_id = str(uuid.uuid4())

        oauth_context = self.oauth_generator.create_oauth_context(
            provider=provider,
            user_id=user_id
        )

        session_data = {
            "session_id": session_id,
            "user_id": user_id,
            "provider": provider,
            "oauth_context": oauth_context,
            "status": "initiated",
            "created_at": datetime.utcnow().isoformat()
        }

        self.active_sessions[session_id] = session_data
        logger.info(f"OAuth flow initiated for {user_id} with {provider} (session: {session_id})")

        return session_data

    async def complete_oauth_flow(self, session_id: str) -> Dict[str, Any]:
        """Simulate completing an OAuth flow."""
        if session_id not in self.active_sessions:
            raise ValueError(f"No active session found: {session_id}")

        session_data = self.active_sessions[session_id]
        session_data["status"] = "completed"
        session_data["completed_at"] = datetime.utcnow().isoformat()

        logger.info(f"OAuth flow completed for session: {session_id}")
        return session_data

    async def send_oauth_authenticated_message(
        self,
        message: str,
        user_id: str,
        provider: str = "google"
    ) -> Dict[str, Any]:
        """Send a message with OAuth authentication context."""
        from .test_client import AuthenticatedTestClient

        oauth_context = self.oauth_generator.create_oauth_context(
            provider=provider,
            user_id=user_id
        )

        client = AuthenticatedTestClient(self.agent_base_url)
        return await client.send_authenticated_message(
            message=message,
            user_id=user_id,
            oauth_context=oauth_context
        )

    def create_test_scenarios(self) -> Dict[str, Dict[str, Any]]:
        """Create a set of standard test scenarios for authentication testing."""
        return {
            "valid_bearer_token": {
                "type": "bearer",
                "token": self.token_generator.create_test_token(),
                "expected_result": "success"
            },
            "expired_bearer_token": {
                "type": "bearer",
                "token": self.token_generator.create_expired_token(),
                "expected_result": "failure"
            },
            "invalid_bearer_token": {
                "type": "bearer",
                "token": self.token_generator.create_invalid_token(),
                "expected_result": "failure"
            },
            "google_oauth": {
                "type": "oauth",
                "context": self.oauth_generator.create_oauth_context("google"),
                "expected_result": "success"
            },
            "github_oauth": {
                "type": "oauth",
                "context": self.oauth_generator.create_oauth_context("github"),
                "expected_result": "success"
            }
        }


class AuthAssertions:
    """Helper class for making authentication-related assertions in tests."""

    @staticmethod
    def assert_auth_context_forwarded(response: Dict[str, Any], agent_name: str):
        """Assert that authentication context was properly forwarded."""
        assert response.get("success"), f"Request failed: {response}"

        response_text = response.get("message", "").lower()

        # Check for auth forwarding indicators
        auth_indicators = [
            "authentication context received",
            "bearer token successfully forwarded",
            f"{agent_name}_auth_verified",
            "auth context verification",
            "authentication verified"
        ]

        auth_forwarded = any(indicator in response_text for indicator in auth_indicators)
        assert auth_forwarded, f"Authentication not properly forwarded to {agent_name}. Response: {response_text}"

    @staticmethod
    def assert_bearer_token_present(response: Dict[str, Any]):
        """Assert that bearer token was present in the forwarded context."""
        response_data = response.get("response", {})

        # Look for token indicators in various response formats
        token_indicators = [
            "token_present",
            "bearer_token",
            "authorization",
            "auth_type"
        ]

        found_token_indicator = False
        for key in token_indicators:
            if key in str(response_data).lower():
                found_token_indicator = True
                break

        assert found_token_indicator, f"Bearer token not found in response: {response_data}"

    @staticmethod
    def assert_oauth_context_present(response: Dict[str, Any], provider: str):
        """Assert that OAuth context was present in the forwarded context."""
        response_data = response.get("response", {})
        response_text = str(response_data).lower()

        oauth_indicators = [
            "oauth_context",
            f"provider: {provider}",
            "oauth_authenticated",
            "user_info"
        ]

        found_oauth_indicator = False
        for indicator in oauth_indicators:
            if indicator.lower() in response_text:
                found_oauth_indicator = True
                break

        assert found_oauth_indicator, f"OAuth context for {provider} not found in response: {response_data}"