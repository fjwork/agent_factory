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
    Extract auth context from global registry and directly update remote agents' HTTP clients.

    This callback:
    1. Extracts auth context from global registry (stored by handlers.py)
    2. Directly accesses and modifies remote agents via callback_context
    3. Updates RemoteA2aAgent HTTP clients with authentication headers
    """
    try:
        agent = callback_context._invocation_context.agent

        # Extract auth context from global registry instead of session state
        auth_context = _extract_auth_from_global_registry()

        if auth_context:
            logger.debug(f"Extracted auth context for user: {auth_context.get('user_id')}")

            # Directly access and update remote agents via sub_agents
            if hasattr(agent, 'sub_agents') and agent.sub_agents:
                logger.debug(f"Found {len(agent.sub_agents)} remote agents to update")

                for sub_agent in agent.sub_agents:
                    try:
                        # Update the HTTP client headers directly for RemoteA2aAgent
                        # Based on ADK source: RemoteA2aAgent stores HTTP client in _httpx_client
                        if hasattr(sub_agent, '_httpx_client') and sub_agent._httpx_client:
                            # Create auth headers
                            auth_headers = {
                                "Authorization": f"Bearer {auth_context.get('token')}",
                                "User-Agent": f"agent-template-root-agent/{sub_agent.name}",
                                "X-Forwarded-Auth-Type": auth_context.get('auth_type', 'bearer'),
                                "X-Forwarded-User-ID": auth_context.get('user_id', ''),
                                "X-Forwarded-Auth-Provider": auth_context.get('provider', '')
                            }

                            # Update headers on existing HTTP client
                            sub_agent._httpx_client.headers.update(auth_headers)
                            logger.info(f"✅ Updated {sub_agent.name} HTTP client with auth headers")

                        else:
                            logger.warning(f"No _httpx_client found on remote agent {sub_agent.name}")

                    except Exception as sub_e:
                        logger.error(f"Failed to update remote agent {getattr(sub_agent, 'name', 'unknown')}: {sub_e}")

            else:
                logger.debug("No remote agents (sub_agents) found to update")

            logger.debug("Completed direct remote agent auth update")
        else:
            logger.debug("No auth context found in global registry - remote agents will use default clients")

    except Exception as e:
        logger.error(f"Auth context callback failed: {e}")
        # Don't fail the request if callback fails

    return None

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