# Authentication Forwarding Implementation Plan
**Using `before_agent_callback` + `httpx_client` Approach**

## Current State Analysis

### ✅ What's Working
- **OAuth flow**: Device flow + bearer token validation working perfectly
- **Auth extraction**: `DualAuthMiddleware` successfully extracts auth context from requests
- **Bearer token validation**: Supports JWT validation and testing modes
- **Session management**: OAuth context stored in session state for tools

### ❌ Current Problems
- **RemoteA2aAgent auth forwarding fails**: Lines 186-205 in `remote_agent_factory.py` don't work
- **Agent reloading causes timing issues**: `reload_agent_with_auth_context()` in `agent.py:100-141`
- **Auth context not reaching remote agents**: Created but never actually forwarded

### 🔍 Key Discovery
**RemoteA2aAgent DOES support `httpx_client` parameter!** (Line 126 in ADK source)
- Constructor accepts `httpx_client: Optional[httpx.AsyncClient] = None`
- Also supports `a2a_client_factory` with httpx client configuration
- **No monkey patching needed** - clean, supported approach!

## Current Architecture

```
[Web Request] → [DualAuthMiddleware] → [AuthenticatedRequestHandler] → [Agent] → [RemoteA2aAgent]
     ↓                    ↓                          ↓                   ↓             ↓
 Bearer Token    Extract Context         Store in Session    Agent Reload    ❌ No Auth
```

**Problem**: Auth context stops at agent level, never reaches RemoteA2aAgent

## Proposed Solution: `before_agent_callback` + `httpx_client`

### Core Concept
1. **Use `before_agent_callback`** to intercept agent execution before each remote call
2. **Extract auth context** from request/session state
3. **Create authenticated `httpx.AsyncClient`** with auth headers
4. **Pass client to RemoteA2aAgent** constructor or update existing agents

### Architecture Flow
```
[Web Request] → [DualAuthMiddleware] → [AuthenticatedRequestHandler] → [Agent with before_agent_callback] → [RemoteA2aAgent with auth httpx_client]
     ↓                    ↓                          ↓                                    ↓                              ↓
 Bearer Token    Extract Context         Store in Request State            Extract + Create Client           ✅ Auth Headers
```

## Implementation Plan - MINIMAL CHANGES APPROACH

**Goal**: Minimal changes to working code. Only modify the broken auth forwarding part.

### What NOT to Change
- ✅ **Keep existing OAuth flow** - `DualAuthMiddleware` works perfectly
- ✅ **Keep session storage** - `_store_oauth_in_session_state` method works
- ✅ **Keep auth extraction** - All existing auth patterns work
- ✅ **Keep agent reloading approach** - Fix it instead of replacing it

### What TO Change
- ❌ **Only fix the broken part**: RemoteA2aAgent creation in `remote_agent_factory.py`
- ❌ **Make agent reloading actually work**: Use the correct `httpx_client` parameter

### Phase 1: Fix Remote Agent Factory + Add Auth Callback (MINIMAL CHANGES)

**CRITICAL INSIGHT**: We need BOTH parts of the solution:
1. **Fix RemoteA2aAgent creation** - Use correct `httpx_client` parameter
2. **Add before_agent_callback** - Extract auth context from session at runtime

**Why both are needed**:
- Current `reload_agent_with_auth_context()` in `agent.py:100-141` runs but doesn't have access to current request's auth context
- `before_agent_callback` runs per agent execution and can access session state where auth context is stored
- RemoteA2aAgent fix ensures the auth actually gets forwarded

#### 1.1 Fix RemoteA2aAgent Creation (ONE FILE, ONE LINE)
**File**: `src/agent_factory/remote_agent_factory.py` (REPLACE LINE 189)

**Current broken code**:
```python
# Lines 186-205 - THIS DOESN'T WORK!
if http_client:
    # Try to create with custom HTTP client (this might not be supported by ADK)
    remote_agent = RemoteA2aAgent(
        name=name,
        description=description,
        agent_card=agent_card_url
    )
    # Try to set the HTTP client if the agent has that capability
    if hasattr(remote_agent, '_http_client') or hasattr(remote_agent, 'http_client'):
        # ... this fails because RemoteA2aAgent doesn't expose these attributes
```

**NEW working code** (replace lines 186-225):
```python
        # Create the RemoteA2aAgent with httpx_client parameter (ADK supports this!)
        try:
            remote_agent = RemoteA2aAgent(
                name=name,
                description=description,
                agent_card=agent_card_url,
                httpx_client=http_client  # THIS IS THE FIX!
            )

            if http_client:
                logger.info(f"✅ Created {name} with authenticated HTTP client")
            else:
                logger.info(f"📱 Created {name} with default HTTP client")

        except Exception as e:
            logger.error(f"Failed to create RemoteA2aAgent: {e}")
            # Fallback to standard creation
            remote_agent = RemoteA2aAgent(
                name=name,
                description=description,
                agent_card=agent_card_url
            )
            # Clean up unused client
            if http_client:
                await http_client.aclose()

        return remote_agent

#### 1.2 Add before_agent_callback for Token Access (ESSENTIAL!)
**File**: `src/auth/agent_auth_callback.py` (NEW FILE)

**Why this is needed**: Your existing `reload_agent_with_auth_context()` can't access the current request's auth context. The callback can extract it from session state where your handlers store it.

```python
"""
Authentication callback for extracting auth context from session state.

This callback bridges the gap between:
1. Auth context stored in session state by handlers.py
2. Agent reloading that needs current request's auth context
"""
import logging
import asyncio
from typing import Optional, Dict, Any
from google.adk.agents.callback_context import CallbackContext
from google.genai import types

logger = logging.getLogger(__name__)

def auth_context_callback(callback_context: CallbackContext) -> Optional[types.Content]:
    """
    Extract auth context from session and trigger agent reloading with auth.

    This callback:
    1. Extracts auth context from ADK session state (stored by handlers.py)
    2. Calls existing reload_agent_with_auth_context() with extracted context
    3. Ensures RemoteA2aAgent instances get authenticated HTTP clients
    """
    try:
        agent = callback_context._invocation_context.agent
        session = callback_context._invocation_context.session

        # Extract auth context from session state
        auth_context = _extract_auth_from_session_state(session)

        if auth_context:
            logger.debug(f"Extracted auth context for user: {auth_context.get('user_id')}")

            # Use existing reload function with extracted auth context
            from agent import reload_agent_with_auth_context

            # Create task to reload agent with auth context
            # This will update RemoteA2aAgent instances with authenticated HTTP clients
            asyncio.create_task(reload_agent_with_auth_context(agent, auth_context))

            logger.debug("Triggered agent reload with auth context")
        else:
            logger.debug("No auth context found in session - remote agents will use default clients")

    except Exception as e:
        logger.error(f"Auth context callback failed: {e}")
        # Don't fail the request if callback fails

    return None

def _extract_auth_from_session_state(session) -> Optional[Dict[str, Any]]:
    """
    Extract authentication context from ADK session state.

    This reads the auth context stored by _store_oauth_in_session_state()
    in handlers.py (lines 364-451).
    """
    try:
        if not session or not hasattr(session, 'state') or not session.state:
            logger.debug("No session state available")
            return None

        state = session.state

        # Check for OAuth context (stored by handlers.py)
        if state.get('oauth_authenticated'):
            return {
                'user_id': state.get('oauth_user_id'),
                'provider': state.get('oauth_provider'),
                'token': state.get('oauth_token'),
                'user_info': state.get('oauth_user_info', {}),
                'authenticated': True,
                'auth_type': 'oauth'
            }

        # Check for bearer token context (stored by handlers.py)
        if state.get('bearer_authenticated'):
            return {
                'user_id': state.get('bearer_user_id'),
                'provider': 'bearer_token',
                'token': state.get('bearer_token'),
                'authenticated': True,
                'auth_type': 'bearer'
            }

        # Check for generic auth context
        if state.get('auth_authenticated'):
            return {
                'user_id': state.get('auth_user_id'),
                'provider': state.get('auth_provider'),
                'token': state.get('auth_token'),
                'authenticated': True,
                'auth_type': state.get('auth_type', 'unknown')
            }

        logger.debug("No auth context found in session state")
        return None

    except Exception as e:
        logger.error(f"Failed to extract auth from session state: {e}")
        return None
```

#### 1.3 Update Agent Creation to Use Callback
**File**: `src/agent.py` (MODIFY LINE ~76)

**Current code**:
```python
# Create agent with optional sub-agents
agent = Agent(
    model=model_name,
    name=agent_name,
    instruction=instruction,
    tools=tools,
    sub_agents=remote_agents if remote_agents else None,
    description=f"{agent_name} with OAuth authentication and A2A protocol support"
)
```

**NEW code**:
```python
# Import the callback
from auth.agent_auth_callback import auth_context_callback

# Create agent with optional sub-agents and auth callback
agent = Agent(
    model=model_name,
    name=agent_name,
    instruction=instruction,
    tools=tools,
    sub_agents=remote_agents if remote_agents else None,
    description=f"{agent_name} with OAuth authentication and A2A protocol support",
    before_agent_callback=auth_context_callback  # ADD THIS LINE
)
```

### Complete Solution Summary

**THREE MINIMAL CHANGES NEEDED**:

1. **Fix RemoteA2aAgent** - Use `httpx_client` parameter (1 line change)
2. **Create auth callback** - Extract auth from session (1 new file)
3. **Add callback to agent** - Connect callback to agent (1 line change)

**Why this works**:
- ✅ Your existing auth extraction and HTTP client creation already works
- ✅ Your existing session storage in handlers.py already works
- ✅ Your existing `reload_agent_with_auth_context()` already works
- ✅ Just need to connect them with the callback
- ✅ RemoteA2aAgent constructor accepts `httpx_client` parameter

**Flow after fix**:
1. Request comes in with bearer token
2. `DualAuthMiddleware` extracts auth context ✅ (already works)
3. `AuthenticatedRequestHandler` stores auth in session ✅ (already works)
4. Agent execution starts
5. `before_agent_callback` extracts auth from session ✅ (new)
6. Callback calls `reload_agent_with_auth_context()` ✅ (already works)
7. Remote agent factory creates RemoteA2aAgent with `httpx_client` ✅ (fixed)
8. Remote calls include auth headers ✅ (now works!)

### Optional: Simple Test
**File**: `scripts/test_minimal_fix.py` (NEW, OPTIONAL)

```python
"""Quick test to verify the minimal fix works."""
import asyncio
import httpx
import json

async def test_minimal_fix():
    test_token = "test-token-123"
    a2a_request = {
        "jsonrpc": "2.0",
        "method": "message/send",
        "params": {
            "context_id": "test-context",
            "message": {
                "role": "user",
                "parts": [{"text": "Test remote agent with auth"}]
            }
        },
        "id": 1
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8000/a2a",
            headers={"Authorization": f"Bearer {test_token}"},
            json=a2a_request
        )
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")

if __name__ == "__main__":
    asyncio.run(test_minimal_fix())
```

## Benefits of Minimal Approach

- ✅ **2 files changed** instead of 5+ files
- ✅ **~50 lines of code** instead of 200+ lines
- ✅ **Zero risk** to working OAuth/auth systems
- ✅ **No new dependencies** or patterns
- ✅ **Uses existing ADK patterns** correctly
- ✅ **Maintains all current functionality**
- ✅ **Leverages existing reload logic**

## The Root Cause Analysis

The issue had **two parts**:

### Part 1: RemoteA2aAgent Creation (FIXED)
- ❌ Line 189: Created RemoteA2aAgent WITHOUT `httpx_client` parameter
- ❌ Lines 196-204: Tried to set internal attributes that don't exist
- ✅ **Fix**: Pass `httpx_client` to constructor (RemoteA2aAgent supports this!)

### Part 2: Auth Context Access (MISSING)
- ❌ `reload_agent_with_auth_context()` runs but has no access to current request's auth
- ❌ Auth context is stored in session by handlers.py but not accessible during reload
- ✅ **Fix**: Use `before_agent_callback` to extract auth from session and trigger reload

## Critical Context for Next Session

### What Already Works (DON'T CHANGE)
1. **Auth extraction**: `DualAuthMiddleware.extract_auth_context()` in `dual_auth_middleware.py:36-67`
2. **Session storage**: `_store_oauth_in_session_state()` in `handlers.py:364-451`
3. **HTTP client creation**: Lines 154-172 in `remote_agent_factory.py`
4. **Agent reloading**: `reload_agent_with_auth_context()` in `agent.py:100-141`

### What's Broken (NEEDS FIXING)
1. **RemoteA2aAgent parameter**: Line 189 in `remote_agent_factory.py` - missing `httpx_client=http_client`
2. **Auth context access**: No connection between session auth storage and agent reloading

### Key Implementation Details
1. **Session state format**: Handlers store auth as `oauth_authenticated`, `oauth_user_id`, `oauth_token`, etc.
2. **Callback timing**: `before_agent_callback` runs before each agent execution, has access to session
3. **Existing reload**: `reload_agent_with_auth_context()` expects auth context dict with `token`, `user_id`, etc.

### Testing Approach
- Use `BEARER_TOKEN_VALIDATION=valid` for testing
- Send requests to `http://localhost:8000/a2a` with `Authorization: Bearer <token>`
- Check logs for "✅ Created {name} with authenticated HTTP client"
- Verify remote agent calls include `Authorization` headers

### File Locations
- Auth callback: Create `src/auth/agent_auth_callback.py`
- Agent creation: Modify `src/agent.py` line ~76
- Remote factory: Modify `src/agent_factory/remote_agent_factory.py` line 189

This approach preserves all working code and only fixes the broken connection points.