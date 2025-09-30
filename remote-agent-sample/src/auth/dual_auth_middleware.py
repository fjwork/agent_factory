"""
Dual Authentication Middleware

This module implements the DualAuthMiddleware that supports both:
1. Bearer token authentication (from web apps/orchestrators)
2. OAuth device flow authentication (existing pattern)

The middleware detects the authentication method and provides unified user context.
"""

import os
import logging
import json
import base64
from typing import Dict, Any, Optional
from starlette.requests import Request

from .oauth_middleware import OAuthMiddleware, OAuthError

logger = logging.getLogger(__name__)


class DualAuthMiddleware:
    """
    Enhanced authentication middleware supporting both bearer tokens and OAuth flows.

    Priority order:
    1. Bearer token (from Authorization header)
    2. OAuth session (existing tokens)
    3. Device flow initiation (for new users)
    """

    def __init__(self, oauth_middleware: OAuthMiddleware):
        self.oauth_middleware = oauth_middleware

    async def extract_auth_context(self, request: Request) -> Optional[Dict[str, Any]]:
        """
        Extract authentication context from request.

        Returns unified user context regardless of authentication method.
        """
        try:
            # Priority 1: Bearer token from Authorization header
            bearer_token = self._extract_bearer_header(request)
            if bearer_token:
                logger.debug("Found bearer token in Authorization header")
                return await self._validate_bearer_token(bearer_token)

            # Priority 2: OAuth session context (existing pattern)
            oauth_context = await self._get_oauth_session(request)
            if oauth_context:
                logger.debug("Found existing OAuth session")
                return oauth_context

            # Priority 3: For OAuth flows, check if user context available in body
            user_context_from_body = await self._extract_user_context_from_body(request)
            if user_context_from_body:
                logger.debug("Found user context in request body")
                return user_context_from_body

            # No authentication found - this will require OAuth device flow initiation
            logger.debug("No authentication found - OAuth device flow required")
            return None

        except Exception as e:
            logger.error(f"Error extracting auth context: {e}")
            return None

    def _extract_bearer_header(self, request: Request) -> Optional[str]:
        """Extract bearer token from Authorization header."""
        auth_header = request.headers.get("Authorization", "")

        if auth_header.startswith("Bearer "):
            token = auth_header[7:].strip()
            if token:
                logger.debug(f"Extracted bearer token (length: {len(token)})")
                return token

        return None

    async def _validate_bearer_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Validate bearer token and return normalized user context.

        Uses environment variable BEARER_TOKEN_VALIDATION for testing:
        - "valid": Always return success with mock user data
        - "invalid": Always return None (invalid token)
        - "jwt": Attempt JWT validation (default behavior)
        """
        validation_mode = os.getenv("BEARER_TOKEN_VALIDATION", "jwt").lower()

        try:
            if validation_mode == "valid":
                # Mock validation - always successful for testing
                logger.info("Bearer token validation: MOCK SUCCESS")
                return self._create_mock_bearer_user_context(token)

            elif validation_mode == "invalid":
                # Mock validation - always fails for testing
                logger.info("Bearer token validation: MOCK FAILURE")
                return None

            elif validation_mode == "jwt":
                # Attempt JWT validation
                return await self._validate_jwt_bearer_token(token)

            else:
                logger.warning(f"Unknown validation mode: {validation_mode}, defaulting to JWT")
                return await self._validate_jwt_bearer_token(token)

        except Exception as e:
            logger.error(f"Bearer token validation failed: {e}")
            return None

    def _create_mock_bearer_user_context(self, token: str) -> Dict[str, Any]:
        """Create mock user context for testing bearer token flow."""
        # Extract user info from token if it looks like a JWT, otherwise use mock data
        user_id = "bearer_user@example.com"
        user_name = "Bearer Token User"

        # Try to decode JWT payload for more realistic testing
        try:
            if "." in token:  # Might be a JWT
                # Split JWT parts (we don't verify signature in mock mode)
                parts = token.split(".")
                if len(parts) >= 2:
                    # Decode payload (add padding if needed)
                    payload_part = parts[1]
                    # Add padding if needed for base64 decoding
                    payload_part += "=" * (4 - len(payload_part) % 4)
                    payload = json.loads(base64.urlsafe_b64decode(payload_part))

                    user_id = payload.get("sub", payload.get("email", user_id))
                    user_name = payload.get("name", user_name)

                    logger.debug(f"Extracted user info from JWT: {user_id}")
        except Exception as e:
            logger.debug(f"Could not decode JWT payload (using mock data): {e}")

        return self._normalize_user_context({
            "user_id": user_id,
            "email": user_id,
            "name": user_name,
            "token": token,
            "verified_email": True
        }, auth_type="bearer")

    async def _validate_jwt_bearer_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Validate JWT bearer token using OAuth middleware."""
        try:
            jwt_payload = self.oauth_middleware.validate_jwt_token(token)

            if jwt_payload:
                user_id = jwt_payload.get("sub") or jwt_payload.get("email")
                if not user_id:
                    logger.warning("No user ID found in JWT payload")
                    return None

                user_context = {
                    "user_id": user_id,
                    "email": jwt_payload.get("email"),
                    "name": jwt_payload.get("name"),
                    "token": token,
                    "jwt_payload": jwt_payload,
                    "verified_email": jwt_payload.get("email_verified", False)
                }

                return self._normalize_user_context(user_context, auth_type="bearer")

            return None

        except Exception as e:
            logger.error(f"JWT bearer token validation failed: {e}")
            return None

    async def _get_oauth_session(self, request: Request) -> Optional[Dict[str, Any]]:
        """Get OAuth session context using existing OAuth middleware patterns."""
        try:
            # Check if there's user context in the request body for OAuth flows
            if request.method == "POST":
                body = await request.body()
                if body:
                    data = json.loads(body)
                    user_id = data.get("user_id")

                    if user_id:
                        # Check for valid OAuth token for this user
                        token_data = await self.oauth_middleware.get_valid_token(user_id)
                        if token_data:
                            user_info = await self.oauth_middleware.get_user_info(user_id)

                            oauth_context = {
                                "user_id": user_id,
                                "provider": token_data.provider,
                                "user_info": user_info or {},
                                "token": token_data.access_token,
                                "oauth_token_data": token_data
                            }

                            return self._normalize_user_context(oauth_context, auth_type="oauth")

        except Exception as e:
            logger.debug(f"No OAuth session found: {e}")

        return None

    async def _extract_user_context_from_body(self, request: Request) -> Optional[Dict[str, Any]]:
        """Extract user context from request body (for OAuth flows)."""
        try:
            if request.method == "POST":
                body = await request.body()
                if body:
                    data = json.loads(body)
                    user_id = data.get("user_id")

                    if user_id:
                        return {
                            "type": "user_context",
                            "user_id": user_id
                        }
        except Exception:
            pass

        return None

    def _normalize_user_context(self, auth_data: Dict[str, Any], auth_type: str) -> Dict[str, Any]:
        """
        Normalize authentication data to unified user context format.

        This ensures both OAuth and bearer token flows produce compatible contexts.
        """
        if auth_type == "bearer":
            return {
                "user_id": auth_data.get("user_id"),
                "provider": "bearer_token",  # Or extract from JWT issuer
                "user_info": {
                    "name": auth_data.get("name", "Unknown"),
                    "email": auth_data.get("email", auth_data.get("user_id")),
                    "verified_email": auth_data.get("verified_email", False)
                },
                "token": auth_data.get("token"),
                "auth_type": "bearer",
                "jwt_payload": auth_data.get("jwt_payload"),
                "authenticated": True
            }

        elif auth_type == "oauth":
            return {
                "user_id": auth_data.get("user_id"),
                "provider": auth_data.get("provider", "unknown"),
                "user_info": auth_data.get("user_info", {}),
                "token": auth_data.get("token") or auth_data.get("access_token"),
                "auth_type": "oauth",
                "oauth_token_data": auth_data.get("oauth_token_data"),
                "authenticated": True
            }

        else:
            # Generic normalization
            return {
                "user_id": auth_data.get("user_id"),
                "provider": auth_data.get("provider", "unknown"),
                "user_info": auth_data.get("user_info", {}),
                "token": auth_data.get("token"),
                "auth_type": auth_type,
                "authenticated": True
            }

    async def initiate_device_flow(self, user_id: str, provider_name: Optional[str] = None) -> Dict[str, Any]:
        """Initiate OAuth device flow for users without bearer tokens."""
        try:
            return await self.oauth_middleware.initiate_auth(user_id, provider_name)
        except Exception as e:
            logger.error(f"Failed to initiate device flow: {e}")
            raise OAuthError(f"Authentication initialization failed: {e}")

    def get_authentication_requirements(self) -> Dict[str, Any]:
        """Return supported authentication methods and requirements."""
        return {
            "supported_methods": ["bearer", "oauth_device_flow"],
            "bearer_token": {
                "description": "Pass bearer token in Authorization header",
                "header": "Authorization: Bearer <token>",
                "formats": ["JWT", "OAuth2 access token"]
            },
            "oauth_device_flow": {
                "description": "OAuth device flow for interactive authentication",
                "initiation_required": True,
                "flow_type": "device_flow"
            }
        }

    def is_bearer_token_valid_env(self) -> bool:
        """Check if bearer token validation is set to 'valid' for testing."""
        return os.getenv("BEARER_TOKEN_VALIDATION", "").lower() == "valid"

    def is_bearer_token_invalid_env(self) -> bool:
        """Check if bearer token validation is set to 'invalid' for testing."""
        return os.getenv("BEARER_TOKEN_VALIDATION", "").lower() == "invalid"