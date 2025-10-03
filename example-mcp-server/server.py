"""
Example MCP Server Implementation

This is what you would need to build to complement the MCP toolkit.
The ADK agent connects TO this server using the mcp_toolkit.py I created.
"""

from flask import Flask, request, jsonify
import jwt
import os
import requests

app = Flask(__name__)

def validate_jwt_token(auth_header):
    """Validate JWT token from ADK agent."""
    if not auth_header or not auth_header.startswith('Bearer '):
        raise ValueError("Missing or invalid authorization header")

    token = auth_header.replace('Bearer ', '')

    # In production, validate the JWT properly
    # For demo, we'll just decode without verification
    try:
        payload = jwt.decode(token, options={"verify_signature": False})
        return payload
    except Exception as e:
        raise ValueError(f"Invalid token: {e}")

@app.route('/mcp/tools', methods=['GET'])
def get_tools():
    """Return available tools to the ADK agent."""
    try:
        # Validate authentication
        auth_header = request.headers.get('X-Serverless-Authorization')
        validate_jwt_token(auth_header)

        # Return available tools
        tools = [
            {
                "name": "get_weather",
                "description": "Get current weather for a location",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "location": {
                            "type": "string",
                            "description": "City name or location"
                        }
                    },
                    "required": ["location"]
                }
            },
            {
                "name": "search_news",
                "description": "Search for news articles",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search query"
                        }
                    },
                    "required": ["query"]
                }
            }
        ]

        return jsonify({"tools": tools})

    except Exception as e:
        return jsonify({"error": str(e)}), 401

@app.route('/mcp/call', methods=['POST'])
def call_tool():
    """Execute a tool and return results."""
    try:
        # Validate authentication
        auth_header = request.headers.get('X-Serverless-Authorization')
        user_info = validate_jwt_token(auth_header)

        # Get request data
        data = request.json
        tool_name = data.get('tool')
        parameters = data.get('parameters', {})

        # Execute the requested tool
        if tool_name == 'get_weather':
            result = get_weather_data(parameters.get('location'))
        elif tool_name == 'search_news':
            result = search_news_data(parameters.get('query'))
        else:
            return jsonify({"error": f"Unknown tool: {tool_name}"}), 400

        return jsonify({
            "success": True,
            "result": result,
            "tool": tool_name,
            "user": user_info.get('email', 'unknown')
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

def get_weather_data(location):
    """Actual weather tool implementation."""
    # This is where you'd integrate with a real weather API
    # For demo, return mock data
    return {
        "location": location,
        "temperature": "72°F",
        "condition": "Sunny",
        "humidity": "45%",
        "source": "Mock Weather API"
    }

def search_news_data(query):
    """Actual news search tool implementation."""
    # This is where you'd integrate with a real news API
    # For demo, return mock data
    return {
        "query": query,
        "articles": [
            {
                "title": f"Sample news about {query}",
                "summary": f"This is a mock news article about {query}.",
                "url": "https://example.com/news/1"
            }
        ],
        "source": "Mock News API"
    }

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({"status": "healthy", "service": "MCP Server"})

if __name__ == '__main__':
    port = int(os.getenv('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=True)