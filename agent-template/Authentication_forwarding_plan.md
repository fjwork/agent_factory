 You're absolutely right. Let me create a focused plan specifically for forwarding authentication from the root agent to remote agents, building on your existing OAuth flow.

  Focused Authentication Forwarding Plan

  Current State Analysis

  - ✅ OAuth flow working (device flow + bearer token validation)
  - ✅ Auth context extraction at middleware level
  - ❌ Auth context not properly forwarded to remote agents
  - ❌ ADK's RemoteA2aAgent doesn't expose HTTP client configuration
  - ❌ Agent reloading approach causes timing issues

  Core Problem

  The issue is in /src/agent_factory/remote_agent_factory.py:186-205 where you try to set custom HTTP clients on RemoteA2aAgent, but ADK doesn't expose this interface. The auth headers get created
  but never actually forwarded.

  ---
  Phase 1: HTTP Transport Layer Auth Forwarding (Critical)

  1.1 Replace Agent Reloading with Request-Scoped Auth Context

  Problem: reload_agent_with_auth_context() causes timing issues
  Solution: Store auth context in request state, not agent state

  Files to Modify:
  - src/agent_a2a/handlers.py:585-629 (REMOVE _inject_auth_context_into_agent)
  - src/agent_a2a/handlers.py:78-81 (MODIFY to store in request state)

  Implementation:
  # Modified: handlers.py handle_post method
  async def handle_post(self, request: Request) -> Response:
      user_context = await self.dual_auth_middleware.extract_auth_context(request)

      if not user_context or not user_context.get("authenticated"):
          return JSONResponse({"error": "Authentication required"}, status_code=401)

      # Store auth context in request state for forwarding
      request.state.auth_context = user_context
      request.state.forwarding_headers = self._build_forwarding_headers(user_context)

      # REMOVE: await self._inject_auth_context_into_agent(user_context)

      # Continue with normal A2A processing
      return await super().handle_post(request)

  def _build_forwarding_headers(self, user_context: Dict[str, Any]) -> Dict[str, str]:
      """Build headers for forwarding to remote agents"""
      headers = {}

      token = user_context.get("token") or user_context.get("access_token")
      if token:
          headers["Authorization"] = f"Bearer {token}"

      if user_context.get("user_id"):
          headers["X-Forwarded-User-ID"] = user_context["user_id"]
      if user_context.get("provider"):
          headers["X-Forwarded-Auth-Provider"] = user_context["provider"]

      return headers

  1.2 Create HTTP Client Monkey Patch for ADK

  Problem: ADK's RemoteA2aAgent uses internal HTTP client we can't configure
  Solution: Monkey patch httpx calls to inject auth headers

  Files to Create:
  - src/agent_factory/auth_patch.py (NEW)

  Implementation:
  # New: auth_patch.py
  import httpx
  import functools
  from typing import Dict, Any, Optional
  from contextvars import ContextVar

  # Context variable to store auth headers for current request
  _auth_headers: ContextVar[Optional[Dict[str, str]]] = ContextVar('auth_headers', default=None)

  class AuthPatchedClient:
      """Patches httpx.AsyncClient to inject authentication headers"""

      _original_request = None
      _patched = False

      @classmethod
      def apply_patch(cls):
          """Apply the authentication patch to httpx.AsyncClient"""
          if cls._patched:
              return

          cls._original_request = httpx.AsyncClient.request
          httpx.AsyncClient.request = cls._patched_request
          cls._patched = True

      @classmethod
      def remove_patch(cls):
          """Remove the authentication patch"""
          if not cls._patched or not cls._original_request:
              return

          httpx.AsyncClient.request = cls._original_request
          cls._patched = False

      @classmethod
      async def _patched_request(cls, self, method: str, url, **kwargs):
          """Patched request method that injects auth headers"""

          # Get auth headers from context
          auth_headers = _auth_headers.get()

          if auth_headers:
              # Check if this is a request to a remote agent
              url_str = str(url)
              if cls._is_remote_agent_request(url_str):
                  # Inject auth headers
                  if "headers" not in kwargs:
                      kwargs["headers"] = {}

                  # Convert headers to httpx.Headers if needed
                  if not isinstance(kwargs["headers"], httpx.Headers):
                      kwargs["headers"] = httpx.Headers(kwargs["headers"])

                  # Add auth headers
                  for key, value in auth_headers.items():
                      kwargs["headers"][key] = value

                  # Log the forwarding
                  import logging
                  logger = logging.getLogger(__name__)
                  logger.debug(f"🔐 Forwarding auth to remote agent: {url_str}")

          # Call original request method
          return await cls._original_request(self, method, url, **kwargs)

      @classmethod
      def _is_remote_agent_request(cls, url: str) -> bool:
          """Check if URL is for a remote agent"""
          # Exclude local requests and well-known paths
          if url.startswith("http://localhost") or url.startswith("http://127.0.0.1"):
              return False
          if "/.well-known/" in url:
              return False

          # Include remote HTTP/HTTPS requests
          return url.startswith(("http://", "https://"))

  def set_auth_context_for_request(auth_headers: Dict[str, str]):
      """Set auth headers for current request context"""
      _auth_headers.set(auth_headers)

  def clear_auth_context():
      """Clear auth headers from current request context"""
      _auth_headers.set(None)

  1.3 Integrate Auth Patch with Request Handler

  Files to Modify:
  - src/agent_a2a/handlers.py:44-82 (MODIFY handle_post)
  - src/agent_a2a/server.py (MODIFY to apply patch on startup)

  Implementation:
  # Modified: handlers.py
  from agent_factory.auth_patch import set_auth_context_for_request, clear_auth_context

  async def handle_post(self, request: Request) -> Response:
      try:
          user_context = await self.dual_auth_middleware.extract_auth_context(request)

          if not user_context or not user_context.get("authenticated"):
              return JSONResponse({"error": "Authentication required"}, status_code=401)

          # Set auth context for this request
          forwarding_headers = self._build_forwarding_headers(user_context)
          set_auth_context_for_request(forwarding_headers)

          # Store in request state as well (for other components)
          request.state.auth_context = user_context

          # Process the A2A request normally
          # ADK will now automatically forward auth headers to remote agents
          return await super().handle_post(request)

      finally:
          # Always clear auth context after request
          clear_auth_context()

  Modified: server.py
  # In create_authenticated_a2a_server or AuthenticatedA2AServer.__init__
  from agent_factory.auth_patch import AuthPatchedClient

  def create_authenticated_a2a_server(agent: Agent, **kwargs):
      # Apply auth patch when server starts
      AuthPatchedClient.apply_patch()

      # ... rest of server creation

  ---
  Phase 2: Remote Agent Factory Cleanup

  2.1 Simplify Remote Agent Creation

  Problem: Complex auth injection logic that doesn't work
  Solution: Remove custom HTTP client attempts, rely on patch

  Files to Modify:
  - src/agent_factory/remote_agent_factory.py:112-226 (SIMPLIFY)

  Implementation:
  # Simplified: remote_agent_factory.py
  async def _create_authenticated_remote_agent(self, config: Dict[str, Any], auth_context: Optional[Dict[str, Any]] = None) -> RemoteA2aAgent:
      """Create a RemoteA2aAgent (auth forwarding handled by transport patch)"""

      # Validate required fields
      required_fields = ["name", "description", "agent_card_url"]
      for field in required_fields:
          if field not in config:
              raise ValueError(f"Missing required field '{field}' in remote agent configuration")

      name = config["name"]
      description = config["description"]
      agent_card_url = config["agent_card_url"]

      # Ensure agent card URL has the well-known path
      if not agent_card_url.endswith(AGENT_CARD_WELL_KNOWN_PATH):
          if agent_card_url.endswith('/'):
              agent_card_url = agent_card_url.rstrip('/') + AGENT_CARD_WELL_KNOWN_PATH
          else:
              agent_card_url = agent_card_url + AGENT_CARD_WELL_KNOWN_PATH

      # Create RemoteA2aAgent (auth forwarding handled by httpx patch)
      remote_agent = RemoteA2aAgent(
          name=name,
          description=description,
          agent_card=agent_card_url
      )

      # Log auth forwarding capability
      if auth_context and auth_context.get("authenticated"):
          logger.info(f"🔐 Remote agent {name} configured for auth forwarding")
      else:
          logger.info(f"📱 Remote agent {name} configured (no auth context)")

      return remote_agent

  2.2 Remove Agent Reloading Logic

  Files to Modify:
  - src/agent.py:100-141 (REMOVE reload_agent_with_auth_context)
  - src/agent.py:85-87 (REMOVE _remote_factory storage)

  ---
  Phase 3: Testing and Validation

  3.1 Create Auth Forwarding Test

  Files to Create:
  - tests/test_auth_forwarding.py (NEW)

  Implementation:
  # New: test_auth_forwarding.py
  import pytest
  import httpx
  from unittest.mock import patch, AsyncMock
  from agent_factory.auth_patch import AuthPatchedClient, set_auth_context_for_request

  @pytest.mark.asyncio
  async def test_auth_header_forwarding():
      """Test that auth headers are forwarded to remote agent calls"""

      # Apply the patch
      AuthPatchedClient.apply_patch()

      try:
          # Set auth context
          auth_headers = {
              "Authorization": "Bearer test-token-123",
              "X-Forwarded-User-ID": "user123"
          }
          set_auth_context_for_request(auth_headers)

          # Mock remote agent call
          with patch('httpx.AsyncClient.request', new_callable=AsyncMock) as mock_request:
              mock_request.return_value = httpx.Response(200, json={"success": True})

              # Make a request that would go to remote agent
              async with httpx.AsyncClient() as client:
                  await client.get("https://remote-agent.example.com/test")

              # Verify auth headers were added
              mock_request.assert_called_once()
              call_kwargs = mock_request.call_args[1]
              headers = call_kwargs.get("headers", {})

              assert "Authorization" in headers
              assert headers["Authorization"] == "Bearer test-token-123"
              assert headers["X-Forwarded-User-ID"] == "user123"

      finally:
          AuthPatchedClient.remove_patch()

  3.2 Integration Test Script

  Files to Create:
  - scripts/test_auth_forwarding.py (NEW)

  ---
  Implementation Steps Summary

  1. Remove agent reloading approach (reload_agent_with_auth_context)
  2. Implement HTTP transport patch to inject auth headers into ADK's HTTP calls
  3. Store auth context in request state instead of global agent state
  4. Simplify remote agent factory to rely on transport-level auth forwarding
  5. Test auth header forwarding to remote agents

  Key Benefits

  - ✅ Eliminates timing issues - No agent reloading during requests
  - ✅ Transparent to ADK - Works with existing RemoteA2aAgent
  - ✅ Request-scoped - Auth context isolated per request
  - ✅ Automatic forwarding - All remote agent calls get auth headers
  - ✅ Minimal changes - Builds on existing OAuth infrastructure

  This focused approach solves the core forwarding problem without requiring ADK authentication patterns, working within the existing OAuth flow you've already implemented.
