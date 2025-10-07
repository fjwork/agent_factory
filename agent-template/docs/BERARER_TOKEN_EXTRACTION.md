Technical Documentation: Bearer Token Timing Fix

  Problem Statement

  The Agent Factory template had a critical timing issue where bearer token authentication failed on the first request but worked correctly on subsequent requests. This affected three key
  authentication flows:

  1. Remote Agent Authentication - A2A communication with sub-agents
  2. MCP Toolkit Authentication - Model Context Protocol tool integration
  3. Native Tool Authentication - ADK-based tools via ToolContext

  Root Cause Analysis

  The issue stemmed from the timing of bearer token capture in the authentication flow:

  Broken Flow (Before Fix):
  1. Agent starts → before_agent_callback registered
  2. Request arrives → before_agent_callback runs → Global registry EMPTY → Auth fails
  3. Request processed → Authentication middleware populates registry → Too late
  4. Second request → before_agent_callback runs → Registry has data → Auth works

  Key Issue: The before_agent_callback was attempting to retrieve bearer tokens from a global registry (AuthenticatedRequestHandler._oauth_registry) that was only populated after the callback had
  already executed.

  Architecture Context

  Our authentication architecture differs from standard A2A samples:

  - A2A Samples: Use HTTP middleware for pre-request authentication
  - Our Implementation: Uses agent callbacks for dynamic authentication forwarding
  - Rationale: Enables bearer token forwarding from web apps to tools/remote agents

  Solution Implemented

  Fixed Flow (After Fix):
  1. Request arrives → Authentication succeeds → Bearer token stored IMMEDIATELY
  2. before_agent_callback runs → Registry has token → Auth works ✅
  3. Tools/MCP/Remote agents get token on first request

  Technical Implementation

  Files Modified

  1. agent-template/src/agent_a2a/handlers.py
  - Lines 71-79: Added immediate bearer token capture in handle_post()
  - Lines 497-522: Added _store_bearer_token_in_global_registry() method

  Code Changes Detail

  Change 1: Immediate Token Capture
  # 🎯 CAPTURE BEARER TOKEN IMMEDIATELY - before any callbacks run
  bearer_token = request.headers.get("Authorization", "")
  if bearer_token.startswith("Bearer "):
      token_value = bearer_token.replace("Bearer ", "").strip()
      if token_value:
          user_id = user_context.get("user_id", "default_user")
          self._store_bearer_token_in_global_registry(user_id, token_value, user_context)
          logger.info(f"🎯 Immediately captured bearer token for user: {user_id}")

  Change 2: Registry Storage Method
  def _store_bearer_token_in_global_registry(self, user_id: str, bearer_token: str, user_context: Dict[str, Any]) -> None:
      """Store bearer token in global registry immediately upon authentication."""
      oauth_context = {
          "oauth_user_id": user_context.get("user_id"),
          "oauth_provider": user_context.get("provider", "bearer_token"),
          "oauth_user_info": user_context.get("user_info", {}),
          "oauth_token": bearer_token,  # Store the actual bearer token
          "oauth_authenticated": True,
          "auth_type": user_context.get("auth_type", "bearer")
      }

      if not hasattr(self.__class__, '_oauth_registry'):
          self.__class__._oauth_registry = {}

      self.__class__._oauth_registry[user_id] = oauth_context

  Integration Points

  The fix integrates with existing authentication systems:

  1. Remote Agent Authentication (src/auth/agent_auth_callback.py)
    - Uses _extract_auth_from_global_registry() to get tokens
    - Now finds tokens immediately on first request
  2. MCP Toolkit (src/tools/mcp_toolkit.py)
    - Uses _get_bearer_token_from_registry() for header injection
    - Both initialization-time and callback-time injection now work
  3. Native Tools (via ADK ToolContext)
    - Session state populated via _store_oauth_in_session_state()
    - Global registry serves as backup source

  Testing Verification

  Remote Agent Test:
  curl -X POST http://localhost:8001/ \
    -H "Authorization: Bearer test-token-123" \
    -H "Content-Type: application/json" \
    -d '{"jsonrpc": "2.0", "id": "test-remote-1", "method": "message/send", ...}'

  MCP Toolkit Test:
  curl -X POST http://localhost:8000/ \
    -H "Authorization: Bearer test-token-123" \
    -H "Content-Type: application/json" \
    -d '{"jsonrpc": "2.0", "id": "test-mcp-1", "method": "message/send", ...}'

  Both now work on first request ✅

  Design Decisions

  Why Option 1 (Middleware-Level Capture)?
  - Minimal code changes - low risk of breaking existing functionality
  - Preserves architecture - maintains existing global registry pattern
  - Clear ownership - request handler manages request lifecycle
  - Easy to debug - single location for bearer token logic

  Alternative Approaches Considered:
  - Option 2: Dual Auth Middleware Enhancement (more complex)
  - Option 3: Request State Storage (requires ADK callback modifications)

  Performance Impact

  - Minimal overhead - single additional method call per authenticated request
  - Memory impact - negligible (same data structure, earlier population)
  - Thread safety - uses existing class-level registry pattern

  Security Considerations

  - No security regression - uses same storage mechanism as before
  - Token isolation - tokens stored per-user in registry
  - Logging - bearer tokens are not logged in plaintext (only user IDs)