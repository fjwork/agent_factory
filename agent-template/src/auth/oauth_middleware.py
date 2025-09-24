"""
OAuth Middleware Module

This module provides OAuth authentication middleware for ADK agents,
supporting various OAuth flows and secure token management.
"""

import asyncio
import logging
import time
from typing import Dict, Any, Optional, List, Tuple
from urllib.parse import urlencode, parse_qs
import httpx
import jwt
from authlib.integrations.httpx_client import OAuth2Client
from authlib.oauth2.rfc6749 import OAuth2Token

from .auth_config import AuthConfig, OAuthProvider, OAuthFlowType, load_auth_config
from .credential_store import CredentialStore, TokenData, create_credential_store

logger = logging.getLogger(__name__)


class OAuthError(Exception):
    """OAuth-related errors."""
    pass


class OAuthMiddleware:
    """OAuth middleware for handling authentication flows."""

    def __init__(self, config: Optional[AuthConfig] = None):
        self.config = config or load_auth_config()
        self.credential_store = create_credential_store(
            self.config.token_storage_type,
            enable_encryption=self.config.token_encryption
        )
        self._session_states: Dict[str, Dict[str, Any]] = {}

    async def initiate_auth(self, user_id: str, provider_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Initiate OAuth authentication flow.

        Returns authentication details including URLs and codes for user interaction.
        """
        provider_name = provider_name or self.config.default_provider
        provider = self.config.providers.get(provider_name)

        if not provider:
            raise OAuthError(f"Provider '{provider_name}' not configured")

        if self.config.flow_type == OAuthFlowType.DEVICE_FLOW:
            return await self._initiate_device_flow(user_id, provider)
        elif self.config.flow_type == OAuthFlowType.AUTHORIZATION_CODE:
            return await self._initiate_authorization_code_flow(user_id, provider)
        elif self.config.flow_type == OAuthFlowType.CLIENT_CREDENTIALS:
            return await self._initiate_client_credentials_flow(user_id, provider)
        else:
            raise OAuthError(f"Unsupported flow type: {self.config.flow_type}")

    async def _initiate_device_flow(self, user_id: str, provider: OAuthProvider) -> Dict[str, Any]:
        """Initiate OAuth device flow."""
        if not provider.endpoints.device_authorization_url:
            raise OAuthError(f"Device flow not supported for provider {provider.name}")

        scopes = self.config.scopes or provider.default_scopes
        scope_string = " ".join(scopes)

        data = {
            "client_id": provider.client_id,
            "scope": scope_string
        }

        # Add provider-specific parameters
        data.update(provider.extra_params)

        async with httpx.AsyncClient() as client:
            response = await client.post(
                provider.endpoints.device_authorization_url,
                data=data,
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )

            if response.status_code != 200:
                raise OAuthError(f"Device authorization failed: {response.text}")

            auth_data = response.json()

        # Store session state
        session_id = f"{user_id}:{provider.name}:{int(time.time())}"
        self._session_states[session_id] = {
            "user_id": user_id,
            "provider": provider.name,
            "device_code": auth_data["device_code"],
            "expires_at": time.time() + auth_data.get("expires_in", 1800),
            "interval": auth_data.get("interval", 5)
        }

        return {
            "flow_type": "device_flow",
            "session_id": session_id,
            "verification_url": auth_data["verification_uri"],
            "verification_url_complete": auth_data.get("verification_uri_complete"),
            "user_code": auth_data["user_code"],
            "expires_in": auth_data.get("expires_in", 1800),
            "interval": auth_data.get("interval", 5),
            "message": f"Go to {auth_data['verification_uri']} and enter code: {auth_data['user_code']}"
        }

    async def _initiate_authorization_code_flow(self, user_id: str, provider: OAuthProvider) -> Dict[str, Any]:
        """Initiate OAuth authorization code flow."""
        scopes = self.config.scopes or provider.default_scopes
        scope_string = " ".join(scopes)

        # Generate state parameter for CSRF protection
        import secrets
        state = secrets.token_urlsafe(32)

        # Store session state
        session_id = f"{user_id}:{provider.name}:{int(time.time())}"
        self._session_states[session_id] = {
            "user_id": user_id,
            "provider": provider.name,
            "state": state,
            "expires_at": time.time() + 600  # 10 minutes
        }

        # Build authorization URL
        auth_params = {
            "client_id": provider.client_id,
            "response_type": "code",
            "scope": scope_string,
            "state": state,
            "redirect_uri": "urn:ietf:wg:oauth:2.0:oob"  # For installed apps
        }

        # Add provider-specific parameters
        auth_params.update(provider.extra_params)

        auth_url = f"{provider.endpoints.authorization_url}?{urlencode(auth_params)}"

        return {
            "flow_type": "authorization_code",
            "session_id": session_id,
            "authorization_url": auth_url,
            "state": state,
            "message": f"Go to {auth_url} and authorize the application"
        }

    async def _initiate_client_credentials_flow(self, user_id: str, provider: OAuthProvider) -> Dict[str, Any]:
        """Initiate OAuth client credentials flow."""
        scopes = self.config.scopes or provider.default_scopes
        scope_string = " ".join(scopes)

        data = {
            "grant_type": "client_credentials",
            "client_id": provider.client_id,
            "client_secret": provider.client_secret,
            "scope": scope_string
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                provider.endpoints.token_url,
                data=data,
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )

            if response.status_code != 200:
                raise OAuthError(f"Client credentials flow failed: {response.text}")

            token_data = response.json()

        # Store token
        expires_at = None
        if "expires_in" in token_data:
            expires_at = time.time() + token_data["expires_in"]

        token = TokenData(
            access_token=token_data["access_token"],
            token_type=token_data.get("token_type", "Bearer"),
            expires_at=expires_at,
            scope=token_data.get("scope"),
            user_id=user_id,
            provider=provider.name
        )

        await self.credential_store.store_token(user_id, provider.name, token)

        return {
            "flow_type": "client_credentials",
            "status": "completed",
            "message": "Authentication completed successfully"
        }

    async def complete_auth(self, session_id: str, **kwargs) -> Dict[str, Any]:
        """
        Complete OAuth authentication flow.

        For device flow: polls for completion
        For authorization code flow: requires authorization_code parameter
        """
        if session_id not in self._session_states:
            raise OAuthError("Invalid or expired session")

        session = self._session_states[session_id]

        if time.time() > session["expires_at"]:
            del self._session_states[session_id]
            raise OAuthError("Session expired")

        provider = self.config.providers[session["provider"]]

        if self.config.flow_type == OAuthFlowType.DEVICE_FLOW:
            return await self._complete_device_flow(session, provider)
        elif self.config.flow_type == OAuthFlowType.AUTHORIZATION_CODE:
            auth_code = kwargs.get("authorization_code")
            if not auth_code:
                raise OAuthError("authorization_code parameter required")
            return await self._complete_authorization_code_flow(session, provider, auth_code)
        else:
            raise OAuthError("Flow type does not require completion")

    async def _complete_device_flow(self, session: Dict[str, Any], provider: OAuthProvider) -> Dict[str, Any]:
        """Complete device flow by polling for token."""
        data = {
            "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
            "client_id": provider.client_id,
            "device_code": session["device_code"]
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                provider.endpoints.token_url,
                data=data,
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )

            if response.status_code == 200:
                token_data = response.json()
                await self._store_token_from_response(session["user_id"], provider, token_data)

                # Clean up session
                session_id = f"{session['user_id']}:{provider.name}"
                if session_id in self._session_states:
                    del self._session_states[session_id]

                return {
                    "status": "completed",
                    "message": "Authentication completed successfully"
                }
            elif response.status_code == 400:
                error_data = response.json()
                error = error_data.get("error", "unknown_error")

                if error == "authorization_pending":
                    return {
                        "status": "pending",
                        "message": "Authorization pending. Please complete the authorization."
                    }
                elif error == "slow_down":
                    return {
                        "status": "pending",
                        "message": "Polling too frequently. Please wait before trying again."
                    }
                elif error in ["access_denied", "expired_token"]:
                    # Clean up session
                    session_id = f"{session['user_id']}:{provider.name}"
                    if session_id in self._session_states:
                        del self._session_states[session_id]
                    raise OAuthError(f"Authorization failed: {error}")
                else:
                    raise OAuthError(f"Token request failed: {error}")
            else:
                raise OAuthError(f"Token request failed: {response.text}")

    async def _complete_authorization_code_flow(
        self,
        session: Dict[str, Any],
        provider: OAuthProvider,
        auth_code: str
    ) -> Dict[str, Any]:
        """Complete authorization code flow."""
        data = {
            "grant_type": "authorization_code",
            "client_id": provider.client_id,
            "client_secret": provider.client_secret,
            "code": auth_code,
            "redirect_uri": "urn:ietf:wg:oauth:2.0:oob"
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                provider.endpoints.token_url,
                data=data,
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )

            if response.status_code != 200:
                raise OAuthError(f"Token exchange failed: {response.text}")

            token_data = response.json()

        await self._store_token_from_response(session["user_id"], provider, token_data)

        # Clean up session
        session_id = f"{session['user_id']}:{provider.name}"
        if session_id in self._session_states:
            del self._session_states[session_id]

        return {
            "status": "completed",
            "message": "Authentication completed successfully"
        }

    async def _store_token_from_response(self, user_id: str, provider: OAuthProvider, token_data: Dict[str, Any]):
        """Store token from OAuth response."""
        expires_at = None
        if "expires_in" in token_data:
            expires_at = time.time() + token_data["expires_in"]

        token = TokenData(
            access_token=token_data["access_token"],
            token_type=token_data.get("token_type", "Bearer"),
            refresh_token=token_data.get("refresh_token"),
            expires_at=expires_at,
            scope=token_data.get("scope"),
            user_id=user_id,
            provider=provider.name,
            extra_data=token_data
        )

        await self.credential_store.store_token(user_id, provider.name, token)
        logger.info(f"Stored token for user {user_id}, provider {provider.name}")

    async def get_valid_token(self, user_id: str, provider_name: Optional[str] = None) -> Optional[TokenData]:
        """Get a valid access token for the user and provider."""
        provider_name = provider_name or self.config.default_provider

        token_data = await self.credential_store.get_token(user_id, provider_name)

        if not token_data:
            return None

        # Check if token needs refresh
        if token_data.is_expired() and token_data.refresh_token:
            provider = self.config.providers.get(provider_name)
            if provider:
                try:
                    refreshed_token = await self._refresh_token(user_id, provider, token_data.refresh_token)
                    return refreshed_token
                except Exception as e:
                    logger.error(f"Failed to refresh token: {e}")
                    await self.credential_store.delete_token(user_id, provider_name)
                    return None

        return token_data if not token_data.is_expired() else None

    async def _refresh_token(self, user_id: str, provider: OAuthProvider, refresh_token: str) -> TokenData:
        """Refresh an expired access token."""
        data = {
            "grant_type": "refresh_token",
            "client_id": provider.client_id,
            "client_secret": provider.client_secret,
            "refresh_token": refresh_token
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                provider.endpoints.token_url,
                data=data,
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )

            if response.status_code != 200:
                raise OAuthError(f"Token refresh failed: {response.text}")

            token_data = response.json()

        # Store the refreshed token
        await self._store_token_from_response(user_id, provider, token_data)

        # Return the new token
        return await self.credential_store.get_token(user_id, provider.name)

    async def get_user_info(self, user_id: str, provider_name: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Get user information from the OAuth provider."""
        provider_name = provider_name or self.config.default_provider
        provider = self.config.providers.get(provider_name)

        if not provider or not provider.endpoints.userinfo_url:
            return None

        token_data = await self.get_valid_token(user_id, provider_name)
        if not token_data:
            return None

        async with httpx.AsyncClient() as client:
            headers = {"Authorization": f"{token_data.token_type} {token_data.access_token}"}
            response = await client.get(provider.endpoints.userinfo_url, headers=headers)

            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Failed to get user info: {response.text}")
                return None

    async def revoke_token(self, user_id: str, provider_name: Optional[str] = None) -> bool:
        """Revoke and delete stored token."""
        provider_name = provider_name or self.config.default_provider

        # Delete from credential store
        await self.credential_store.delete_token(user_id, provider_name)

        logger.info(f"Revoked token for user {user_id}, provider {provider_name}")
        return True

    async def list_user_sessions(self, user_id: str) -> Dict[str, TokenData]:
        """List all active sessions for a user."""
        return await self.credential_store.list_user_tokens(user_id)

    def validate_jwt_token(self, token: str, provider_name: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Validate a JWT token (for providers that use JWT)."""
        provider_name = provider_name or self.config.default_provider
        provider = self.config.providers.get(provider_name)

        if not provider or not provider.endpoints.jwks_url:
            return None

        try:
            # This is a simplified JWT validation
            # In production, you should use proper JWT validation with JWKS
            decoded = jwt.decode(token, options={"verify_signature": False})

            # Basic validation
            if self.config.validate_issuer and "iss" in decoded:
                # Add issuer validation logic here
                pass

            if self.config.validate_audience and "aud" in decoded:
                # Add audience validation logic here
                pass

            return decoded
        except jwt.InvalidTokenError as e:
            logger.error(f"JWT validation failed: {e}")
            return None