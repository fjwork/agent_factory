"""
API Example Tool

This tool demonstrates how to make authenticated API calls to external services
using OAuth tokens. It serves as a template for building API integration tools.
"""

import logging
from typing import Dict, Any, Optional
from tools.authenticated_tool import AuthenticatedTool, AuthenticationError, ToolExecutionError

logger = logging.getLogger(__name__)


class APIExampleTool(AuthenticatedTool):
    """Example tool for making authenticated API calls to external services."""

    def __init__(self):
        super().__init__(
            name="api_example_tool",
            description="Makes authenticated API calls to external services using OAuth tokens"
        )

    async def execute_authenticated(
        self,
        user_context: Dict[str, Any],
        api_name: str = "google_userinfo",
        custom_endpoint: Optional[str] = None,
        method: str = "GET",
        data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Make an authenticated API call.

        Args:
            user_context: User authentication context from OAuth
            api_name: Predefined API to call (google_userinfo, google_calendar, etc.)
            custom_endpoint: Custom API endpoint URL (overrides api_name)
            method: HTTP method (GET, POST, PUT, DELETE)
            data: Request data for POST/PUT requests

        Returns:
            API response data
        """
        if not self.validate_user_context(user_context):
            raise AuthenticationError("Invalid user authentication context")

        access_token = self.get_access_token(user_context)
        if not access_token:
            raise AuthenticationError("No access token available")

        self._log_tool_execution(
            user_context,
            "api_call",
            {"api_name": api_name, "method": method, "custom_endpoint": custom_endpoint}
        )

        try:
            # Determine the endpoint URL
            if custom_endpoint:
                endpoint = custom_endpoint
            else:
                endpoint = self._get_predefined_endpoint(api_name)

            if not endpoint:
                raise ToolExecutionError(f"Unknown API name: {api_name}")

            # Make the API call
            response_data = await self._make_api_call(
                endpoint=endpoint,
                access_token=access_token,
                method=method,
                data=data
            )

            return {
                "success": True,
                "api_name": api_name,
                "endpoint": endpoint,
                "method": method,
                "response": response_data,
                "timestamp": self._get_timestamp()
            }

        except Exception as e:
            error_msg = f"API call failed: {str(e)}"
            logger.error(error_msg)
            raise ToolExecutionError(error_msg)

    def _get_predefined_endpoint(self, api_name: str) -> Optional[str]:
        """Get predefined API endpoints for common services."""
        endpoints = {
            "google_userinfo": "https://www.googleapis.com/oauth2/v2/userinfo",
            "google_userinfo_v3": "https://www.googleapis.com/oauth2/v3/userinfo",
            "google_calendar_list": "https://www.googleapis.com/calendar/v3/users/me/calendarList",
            "google_drive_files": "https://www.googleapis.com/drive/v3/files",
            "microsoft_profile": "https://graph.microsoft.com/v1.0/me",
            "microsoft_calendar": "https://graph.microsoft.com/v1.0/me/calendar",
            "github_user": "https://api.github.com/user",
            "github_repos": "https://api.github.com/user/repos"
        }
        return endpoints.get(api_name)

    async def _make_api_call(
        self,
        endpoint: str,
        access_token: str,
        method: str = "GET",
        data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Make the actual API call with proper error handling."""
        try:
            import httpx
        except ImportError:
            raise ToolExecutionError("httpx is required for API calls. Install with: pip install httpx")

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
            "User-Agent": "OAuth-Agent-Template/1.0"
        }

        async with httpx.AsyncClient() as client:
            try:
                if method.upper() == "GET":
                    response = await client.get(endpoint, headers=headers, timeout=30.0)
                elif method.upper() == "POST":
                    response = await client.post(endpoint, headers=headers, json=data, timeout=30.0)
                elif method.upper() == "PUT":
                    response = await client.put(endpoint, headers=headers, json=data, timeout=30.0)
                elif method.upper() == "DELETE":
                    response = await client.delete(endpoint, headers=headers, timeout=30.0)
                else:
                    raise ToolExecutionError(f"Unsupported HTTP method: {method}")

                # Handle different response types
                if response.status_code >= 400:
                    error_detail = ""
                    try:
                        error_detail = response.json()
                    except:
                        error_detail = response.text

                    raise ToolExecutionError(
                        f"API call failed with status {response.status_code}: {error_detail}"
                    )

                # Try to parse JSON response
                try:
                    response_data = response.json()
                except:
                    # If not JSON, return text content
                    response_data = {"content": response.text, "content_type": response.headers.get("content-type")}

                return {
                    "status_code": response.status_code,
                    "headers": dict(response.headers),
                    "data": response_data
                }

            except httpx.TimeoutException:
                raise ToolExecutionError("API call timed out")
            except httpx.RequestError as e:
                raise ToolExecutionError(f"Request failed: {str(e)}")


class GoogleAPIExampleTool(AuthenticatedTool):
    """Specialized example tool for Google API calls."""

    def __init__(self):
        super().__init__(
            name="google_api_example_tool",
            description="Makes calls to various Google APIs using OAuth tokens"
        )

    async def execute_authenticated(
        self,
        user_context: Dict[str, Any],
        service: str = "userinfo",
        action: str = "get",
        resource_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Make Google API calls.

        Args:
            user_context: User authentication context from OAuth
            service: Google service (userinfo, calendar, drive, gmail)
            action: Action to perform (get, list, create, update, delete)
            resource_id: Specific resource ID if needed

        Returns:
            Google API response data
        """
        if not self.validate_user_context(user_context):
            raise AuthenticationError("Invalid user authentication context")

        access_token = self.get_access_token(user_context)
        if not access_token:
            raise AuthenticationError("No access token available")

        provider = self.get_provider(user_context)
        if provider != "google":
            raise AuthenticationError("This tool requires Google OAuth authentication")

        self._log_tool_execution(
            user_context,
            "google_api_call",
            {"service": service, "action": action, "resource_id": resource_id}
        )

        try:
            # Build API endpoint
            endpoint = self._build_google_api_endpoint(service, action, resource_id)
            method = self._get_http_method(action)

            # Make the API call
            response_data = await self._make_google_api_call(
                endpoint=endpoint,
                access_token=access_token,
                method=method
            )

            return {
                "success": True,
                "service": service,
                "action": action,
                "endpoint": endpoint,
                "response": response_data,
                "timestamp": self._get_timestamp()
            }

        except Exception as e:
            error_msg = f"Google API call failed: {str(e)}"
            logger.error(error_msg)
            raise ToolExecutionError(error_msg)

    def _build_google_api_endpoint(self, service: str, action: str, resource_id: Optional[str] = None) -> str:
        """Build Google API endpoint URL."""
        base_urls = {
            "userinfo": "https://www.googleapis.com/oauth2/v2/userinfo",
            "calendar": "https://www.googleapis.com/calendar/v3",
            "drive": "https://www.googleapis.com/drive/v3",
            "gmail": "https://www.googleapis.com/gmail/v1"
        }

        if service == "userinfo":
            return base_urls["userinfo"]
        elif service == "calendar":
            if action == "list":
                return f"{base_urls['calendar']}/users/me/calendarList"
            elif resource_id:
                return f"{base_urls['calendar']}/calendars/{resource_id}"
            else:
                return f"{base_urls['calendar']}/calendars/primary"
        elif service == "drive":
            if action == "list":
                return f"{base_urls['drive']}/files"
            elif resource_id:
                return f"{base_urls['drive']}/files/{resource_id}"
            else:
                return f"{base_urls['drive']}/files"
        elif service == "gmail":
            if action == "list":
                return f"{base_urls['gmail']}/users/me/messages"
            elif resource_id:
                return f"{base_urls['gmail']}/users/me/messages/{resource_id}"
            else:
                return f"{base_urls['gmail']}/users/me/profile"
        else:
            raise ToolExecutionError(f"Unsupported Google service: {service}")

    def _get_http_method(self, action: str) -> str:
        """Get HTTP method for action."""
        method_map = {
            "get": "GET",
            "list": "GET",
            "create": "POST",
            "update": "PUT",
            "delete": "DELETE"
        }
        return method_map.get(action, "GET")

    async def _make_google_api_call(
        self,
        endpoint: str,
        access_token: str,
        method: str = "GET"
    ) -> Dict[str, Any]:
        """Make Google API call with proper error handling."""
        try:
            import httpx
        except ImportError:
            raise ToolExecutionError("httpx is required for API calls. Install with: pip install httpx")

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }

        async with httpx.AsyncClient() as client:
            response = await client.request(method, endpoint, headers=headers, timeout=30.0)

            if response.status_code >= 400:
                try:
                    error_data = response.json()
                    error_msg = error_data.get("error", {}).get("message", "Unknown error")
                except:
                    error_msg = response.text

                raise ToolExecutionError(f"Google API error ({response.status_code}): {error_msg}")

            return {
                "status_code": response.status_code,
                "data": response.json()
            }