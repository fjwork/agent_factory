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
    Inject auth context into ADK session state for tools to access.

    This callback:
    1. Extracts auth context from pending injection store (stored by handlers.py)
    2. Injects auth context directly into the ADK session state
    3. Updates RemoteA2aAgent HTTP clients with authentication headers (for root agents)
    """
    try:
        # Get access to the session from the callback context
        session = callback_context._invocation_context.session
        agent = callback_context._invocation_context.agent

        # Extract auth context from pending injection store
        auth_context = _extract_auth_from_pending_injection()

        if auth_context:
            user_id = auth_context.get('oauth_user_id')  # Use the correct key
            logger.debug(f"Extracted auth context for user: {user_id}")

            # MAIN FEATURE: Inject auth context into ADK session state
            if session and hasattr(session, 'state'):
                try:
                    session.state.update(auth_context)
                    logger.info(f"✅ Injected auth context into ADK session state for user: {user_id}")
                    logger.debug(f"Session state keys after injection: {list(session.state.keys())}")
                except Exception as e:
                    logger.error(f"Failed to inject auth into session state: {e}")

            # SECONDARY: Update remote agents for root agents (if they exist)
            if hasattr(agent, 'sub_agents') and agent.sub_agents:
                logger.debug(f"Found {len(agent.sub_agents)} remote agents to update")

                for sub_agent in agent.sub_agents:
                    try:
                        if hasattr(sub_agent, '_httpx_client') and sub_agent._httpx_client:
                            auth_headers = {
                                "Authorization": f"Bearer {auth_context.get('oauth_token')}",
                                "X-Forwarded-Auth-Type": "bearer",
                                "X-Forwarded-User-ID": user_id or '',
                                "X-Forwarded-Auth-Provider": auth_context.get('oauth_provider', '')
                            }
                            sub_agent._httpx_client.headers.update(auth_headers)
                            logger.info(f"✅ Updated {sub_agent.name} HTTP client with auth headers")
                    except Exception as sub_e:
                        logger.error(f"Failed to update remote agent {getattr(sub_agent, 'name', 'unknown')}: {sub_e}")

            # Clean up pending injection for this user
            _cleanup_pending_injection(user_id)

        else:
            logger.debug("No auth context found in pending injection")

    except Exception as e:
        logger.error(f"Auth context callback failed: {e}")

    return None

def _extract_auth_from_pending_injection() -> Optional[Dict[str, Any]]:
    """
    Extract authentication context from the pending injection store used by handlers.py.
    """
    try:
        from agent_a2a.handlers import AuthenticatedRequestHandler

        if hasattr(AuthenticatedRequestHandler, '_pending_auth_injection'):
            pending_store = AuthenticatedRequestHandler._pending_auth_injection
            if pending_store:
                # Get the most recent auth context
                user_id, auth_context = next(iter(pending_store.items()))
                logger.debug(f"Retrieved pending auth context for user: {user_id}")
                return auth_context
            else:
                logger.debug("Pending injection store is empty")
        else:
            logger.debug("No pending injection store found")

        return None

    except Exception as e:
        logger.error(f"Failed to extract auth from pending injection: {e}")
        return None

def _cleanup_pending_injection(user_id: str):
    """Clean up pending injection for a specific user."""
    try:
        from agent_a2a.handlers import AuthenticatedRequestHandler

        if hasattr(AuthenticatedRequestHandler, '_pending_auth_injection') and user_id:
            pending_store = AuthenticatedRequestHandler._pending_auth_injection
            if user_id in pending_store:
                del pending_store[user_id]
                logger.debug(f"Cleaned up pending injection for user: {user_id}")

    except Exception as e:
        logger.error(f"Failed to cleanup pending injection: {e}")

def _extract_auth_from_global_registry() -> Optional[Dict[str, Any]]:
    """
    Extract authentication context from the global registry used by handlers.py.

    This accesses the module-level _oauth_registry from AuthenticatedRequestHandler.
    """
    try:
        # Import the handler class to access its global registry
        from agent_a2a.handlers import AuthenticatedRequestHandler

        # Check if the registry exists and has any entries
        if hasattr(AuthenticatedRequestHandler, '_oauth_registry'):
            registry = AuthenticatedRequestHandler._oauth_registry
            logger.debug(f"Global registry contains {len(registry)} entries")

            # For now, get the first/most recent user's auth context
            # In production, you might want to match by specific user_id
            if registry:
                # Get the most recent auth context (assuming latest is most relevant)
                user_id, oauth_context = next(iter(registry.items()))
                logger.debug(f"Retrieved auth context for user: {user_id}")

                # Convert to our expected format
                return {
                    'user_id': oauth_context.get('oauth_user_id'),
                    'provider': oauth_context.get('oauth_provider'),
                    'token': oauth_context.get('oauth_token'),
                    'user_info': oauth_context.get('oauth_user_info', {}),
                    'authenticated': oauth_context.get('oauth_authenticated', True),
                    'auth_type': 'bearer'  # Assuming bearer token for now
                }
            else:
                logger.debug("Global registry is empty")
                return None
        else:
            logger.debug("No global registry found on AuthenticatedRequestHandler")
            return None

    except Exception as e:
        logger.error(f"Failed to extract auth from global registry: {e}")
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