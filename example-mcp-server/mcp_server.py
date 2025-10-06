#!/usr/bin/env python3
"""
Proper MCP Server Implementation

This server implements the Model Context Protocol (MCP) using FastMCP
to provide weather and news tools with JWT authentication support.
"""

import asyncio
import os
import logging
from typing import Any, Dict, Optional
import jwt
from datetime import datetime

from fastmcp import FastMCP
from fastmcp.server.dependencies import get_http_headers
from mcp.shared.exceptions import McpError
from mcp.types import INVALID_PARAMS, ErrorData
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Create FastMCP server with proper configuration
server = FastMCP(
    name="weather-news-server",
    instructions="Weather and news tools with JWT authentication",
    port=8080,
    host="0.0.0.0",
    streamable_http_path="/mcp",
    debug=True,
    log_level="INFO"
)

def validate_tokens(headers: Dict[str, str]) -> Dict[str, Any]:
    """
    Validate both JWT token and original bearer token from request headers.

    Args:
        headers: The request headers dict

    Returns:
        Dict containing validation results for both tokens
    """
    result = {
        "jwt_auth": None,
        "bearer_auth": None,
        "primary_auth": None
    }

    # Validate JWT token (primary authentication)
    jwt_result = validate_jwt_token(headers)
    result["jwt_auth"] = jwt_result
    result["primary_auth"] = jwt_result  # JWT remains primary

    # Check for original bearer token (passthrough)
    original_bearer = headers.get("x-original-bearer-token")
    if original_bearer:
        result["bearer_auth"] = {
            "token_present": True,
            "token_value": original_bearer,
            "validation": "passthrough - not validated in this example"
        }
        logger.info(f"Received original bearer token: {original_bearer}")
    else:
        result["bearer_auth"] = {"token_present": False}

    return result


def validate_jwt_token(headers: Dict[str, str]) -> Optional[Dict[str, Any]]:
    """
    Validate JWT token from request headers.

    Args:
        headers: The request headers dict

    Returns:
        Dict containing user info if valid, None if invalid
    """
    try:
        # Check for JWT token in various headers
        auth_header = (
            headers.get("x-serverless-authorization") or
            headers.get("authorization") or
            headers.get("x-auth-token")
        )

        if not auth_header:
            logger.warning("No authorization header found")
            return None

        # Remove Bearer prefix if present
        token = auth_header.replace("Bearer ", "").strip()

        if not token:
            logger.warning("Empty token after processing")
            return None

        # For development/testing, decode without verification
        # In production, you would verify the signature properly
        try:
            payload = jwt.decode(token, options={"verify_signature": False})
            logger.info(f"JWT validated for user: {payload.get('email', 'unknown')}")
            return payload
        except jwt.InvalidTokenError as e:
            logger.error(f"JWT decode error: {e}")
            return None

    except Exception as e:
        logger.error(f"Token validation error: {e}")
        return None

def get_weather_data(location: str) -> Dict[str, Any]:
    """
    Get weather data for a location.

    Args:
        location: The location to get weather for

    Returns:
        Weather data dictionary
    """
    # Mock weather data - in production, you'd call a real weather API
    weather_data = {
        "location": location,
        "temperature": "72°F",
        "condition": "Partly Cloudy",
        "humidity": "65%",
        "wind_speed": "8 mph",
        "forecast": "Pleasant weather expected throughout the day",
        "timestamp": datetime.now().isoformat()
    }

    logger.info(f"Generated weather data for {location}")
    return weather_data

def search_news_data(query: str) -> Dict[str, Any]:
    """
    Search for news articles.

    Args:
        query: The search query

    Returns:
        News data dictionary
    """
    # Mock news data - in production, you'd call a real news API
    news_data = {
        "query": query,
        "articles": [
            {
                "title": f"Breaking: Latest developments in {query}",
                "summary": f"Recent news about {query} showing significant progress...",
                "source": "Tech News Daily",
                "published": datetime.now().isoformat()
            },
            {
                "title": f"Analysis: The impact of {query} on industry",
                "summary": f"Experts weigh in on how {query} is changing the landscape...",
                "source": "Industry Weekly",
                "published": datetime.now().isoformat()
            }
        ],
        "total_results": 2,
        "timestamp": datetime.now().isoformat()
    }

    logger.info(f"Generated news data for query: {query}")
    return news_data

@server.tool()
async def get_weather(location: str) -> Dict[str, Any]:
    """
    Get current weather information for a location.

    Args:
        location: The city or location to get weather for

    Returns:
        Weather information including temperature, conditions, and forecast
    """
    # Validate authentication (both JWT and bearer token)
    try:
        headers = get_http_headers()
        auth_result = validate_tokens(headers)

        # Check JWT authentication (primary)
        if not auth_result["primary_auth"]:
            return {
                "error": "Authentication required for weather data",
                "location": location
            }

        user_info = auth_result["primary_auth"]
    except Exception as e:
        logger.error(f"Error accessing request headers: {e}")
        return {
            "error": f"Request header error: {str(e)}",
            "location": location
        }

    logger.info(f"Weather request from user {user_info.get('email', 'unknown')} for location: {location}")

    try:
        weather_data = get_weather_data(location)

        # Add detailed authentication information (both JWT and bearer token)
        weather_data["authentication_context"] = {
            "authenticated_user": user_info.get("email", "unknown"),
            "primary_auth_method": "JWT",
            "jwt_valid": True,
            "jwt_user_info": {
                "email": user_info.get("email", "unknown"),
                "iat": user_info.get("iat"),
                "exp": user_info.get("exp"),
                "aud": user_info.get("aud"),
                "iss": user_info.get("iss")
            },
            "bearer_token_info": auth_result["bearer_auth"]
        }
        return weather_data
    except Exception as e:
        logger.error(f"Error getting weather data: {e}")
        raise McpError(
            ErrorData(
                code=INVALID_PARAMS.code,
                message=f"Failed to get weather data: {str(e)}"
            )
        )

@server.tool()
async def search_news(query: str) -> Dict[str, Any]:
    """
    Search for news articles on a specific topic.

    Args:
        query: The search query or topic

    Returns:
        News articles and information related to the query
    """
    # Validate authentication (both JWT and bearer token)
    try:
        headers = get_http_headers()
        auth_result = validate_tokens(headers)

        # Check JWT authentication (primary)
        if not auth_result["primary_auth"]:
            return {
                "error": "Authentication required for news search",
                "query": query
            }

        user_info = auth_result["primary_auth"]
    except Exception as e:
        logger.error(f"Error accessing request headers: {e}")
        return {
            "error": f"Request header error: {str(e)}",
            "query": query
        }

    logger.info(f"News search from user {user_info.get('email', 'unknown')} for query: {query}")

    try:
        news_data = search_news_data(query)

        # Add detailed authentication information (both JWT and bearer token)
        news_data["authentication_context"] = {
            "authenticated_user": user_info.get("email", "unknown"),
            "primary_auth_method": "JWT",
            "jwt_valid": True,
            "jwt_user_info": {
                "email": user_info.get("email", "unknown"),
                "iat": user_info.get("iat"),
                "exp": user_info.get("exp"),
                "aud": user_info.get("aud"),
                "iss": user_info.get("iss")
            },
            "bearer_token_info": auth_result["bearer_auth"]
        }
        return news_data
    except Exception as e:
        logger.error(f"Error searching news: {e}")
        raise McpError(
            ErrorData(
                code=INVALID_PARAMS.code,
                message=f"Failed to search news: {str(e)}"
            )
        )

@server.tool()
async def health_check() -> Dict[str, Any]:
    """
    Health check endpoint for monitoring server status.

    Returns:
        Server health and status information
    """
    return {
        "status": "healthy",
        "server": "weather-news-mcp-server",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat(),
        "tools_available": ["get_weather", "search_news", "health_check"]
    }

@server.tool()
async def simple_test() -> Dict[str, Any]:
    """
    Simple test tool without authentication for debugging.

    Returns:
        Simple success message
    """
    logger.info("Simple test tool called - no authentication required")
    return {
        "status": "success",
        "message": "Simple test tool working",
        "timestamp": datetime.now().isoformat()
    }

def main():
    """Main entry point for the MCP server."""
    try:
        logger.info("Starting MCP Server...")
        logger.info("Available tools: get_weather, search_news, health_check")
        logger.info("MCP endpoint: http://localhost:8080/mcp")
        logger.info("Health check: Use MCP protocol")

        # Run the FastMCP server with streamable-http transport
        server.run(transport="streamable-http")

    except Exception as e:
        logger.error(f"Failed to start MCP server: {e}")
        raise

if __name__ == "__main__":
    main()