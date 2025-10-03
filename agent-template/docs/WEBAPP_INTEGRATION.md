# Web Application Integration Guide

This document explains how web applications can integrate with the agent template's authentication system, covering both unauthenticated and authenticated user scenarios.

## Overview

The agent template supports **two primary integration patterns** for web applications:

1. **Bearer Token Authentication** - Seamless integration using existing web app authentication
2. **OAuth Device Flow** - Interactive authentication for unauthenticated users

Both patterns provide secure, user-friendly ways to integrate agent capabilities into web applications while maintaining the flexibility to handle various authentication states.

## Authentication Flow Analysis

### 🔍 **How Unauthenticated Requests Are Handled**

When a web application sends an unauthenticated request to the agent, the system responds with clear guidance on available authentication methods.

#### **Request Flow:**
```
Web App Request → Agent Authentication Check → 401 Response with Auth Options
```

#### **Example: Unauthenticated Request**
```javascript
// Web app makes request without authentication
const response = await fetch('http://localhost:8001/', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({
    jsonrpc: "2.0",
    id: "1",
    method: "message/send",
    params: {
      message: {
        messageId: "msg-1",
        role: "user",
        parts: [{text: "Hello from web app"}]
      }
    }
  })
});

// Agent responds with 401 and authentication requirements
{
  "error": "Authentication required",
  "message": "This endpoint requires authentication",
  "supported_methods": ["bearer", "oauth_device_flow"],
  "details": {
    "bearer_token": {
      "description": "Pass bearer token in Authorization header",
      "header": "Authorization: Bearer <token>",
      "formats": ["JWT", "OAuth2 access token"]
    },
    "oauth_device_flow": {
      "description": "OAuth device flow for interactive authentication",
      "initiation_required": true,
      "flow_type": "device_flow"
    }
  }
}
```

## Integration Patterns

### 🎯 **Pattern A: Bearer Token Integration (Recommended)**

**Best for:** Web applications with existing user authentication systems.

#### **Implementation:**
```javascript
class AgentClient {
  constructor(authService) {
    this.authService = authService;
    this.agentEndpoint = 'http://localhost:8001/';
  }

  async sendMessage(message) {
    // Get JWT token from existing web app authentication
    const userToken = await this.authService.getCurrentUserToken();

    const response = await fetch(this.agentEndpoint, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${userToken}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        jsonrpc: "2.0",
        id: crypto.randomUUID(),
        method: "message/send",
        params: {
          message: {
            messageId: crypto.randomUUID(),
            role: "user",
            parts: [{text: message}]
          }
        }
      })
    });

    if (!response.ok) {
      throw new Error(`Agent request failed: ${response.status}`);
    }

    return await response.json();
  }
}

// Usage in web app
const agentClient = new AgentClient(webAppAuthService);
const result = await agentClient.sendMessage("Analyze my sales data");
```

#### **Benefits:**
- ✅ **Seamless user experience** - No additional authentication steps
- ✅ **Security** - Uses existing web app authentication tokens
- ✅ **Simple integration** - Single API call
- ✅ **No user interaction** - Authentication handled transparently

### 🔄 **Pattern B: OAuth Device Flow Integration**

**Best for:** Web applications that need to authenticate users specifically for agent access, or as a fallback when bearer tokens aren't available.

#### **Complete Implementation:**
```javascript
class AgentOAuthClient {
  constructor(agentEndpoint = 'http://localhost:8001') {
    this.agentEndpoint = agentEndpoint;
    this.authSessions = new Map(); // Store auth sessions per user
  }

  async sendMessage(message, userId) {
    // Check if user is already authenticated
    if (await this.isUserAuthenticated(userId)) {
      return await this.sendAuthenticatedMessage(message, userId);
    }

    // Initiate OAuth flow for unauthenticated user
    await this.authenticateUser(userId);
    return await this.sendAuthenticatedMessage(message, userId);
  }

  async isUserAuthenticated(userId) {
    try {
      const response = await fetch(`${this.agentEndpoint}auth/status?user_id=${userId}`);
      const status = await response.json();
      return status.authenticated;
    } catch (error) {
      return false;
    }
  }

  async authenticateUser(userId) {
    // Step 1: Initiate OAuth device flow
    const authResponse = await fetch(`${this.agentEndpoint}auth/initiate`, {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({
        user_id: userId,
        provider: "google"
      })
    });

    if (!authResponse.ok) {
      throw new Error('Failed to initiate authentication');
    }

    const authData = await authResponse.json();

    // Step 2: Show OAuth flow to user
    await this.showOAuthFlow(authData);

    // Step 3: Poll for completion
    await this.pollForCompletion(authData.session_id);
  }

  async showOAuthFlow(authData) {
    return new Promise((resolve) => {
      // Create modal or redirect user to OAuth page
      const modal = document.createElement('div');
      modal.innerHTML = `
        <div class="oauth-modal">
          <h3>Authentication Required</h3>
          <p>To continue, please authenticate with Google:</p>
          <ol>
            <li>Visit: <a href="${authData.verification_url}" target="_blank">${authData.verification_url}</a></li>
            <li>Enter code: <strong>${authData.user_code}</strong></li>
            <li>Authorize the application</li>
          </ol>
          <p>This window will close automatically when authentication is complete.</p>
          <button onclick="this.parentElement.parentElement.remove()">Cancel</button>
        </div>
      `;

      document.body.appendChild(modal);

      // Store session for polling
      this.authSessions.set(authData.session_id, {
        resolve,
        expiresAt: Date.now() + (authData.expires_in * 1000)
      });
    });
  }

  async pollForCompletion(sessionId) {
    const session = this.authSessions.get(sessionId);
    if (!session) return;

    const poll = async () => {
      try {
        const response = await fetch(`${this.agentEndpoint}auth/complete`, {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({session_id: sessionId})
        });

        const result = await response.json();

        if (result.status === "completed") {
          // Authentication successful
          this.authSessions.delete(sessionId);
          session.resolve();
          this.closeAuthModal();
        } else if (result.status === "pending") {
          // Still waiting for user to complete OAuth
          if (Date.now() < session.expiresAt) {
            setTimeout(poll, 5000); // Poll every 5 seconds
          } else {
            // Session expired
            this.authSessions.delete(sessionId);
            throw new Error('Authentication session expired');
          }
        } else {
          // Authentication failed
          this.authSessions.delete(sessionId);
          throw new Error(`Authentication failed: ${result.error || 'Unknown error'}`);
        }
      } catch (error) {
        this.authSessions.delete(sessionId);
        throw error;
      }
    };

    setTimeout(poll, 2000); // Start polling after 2 seconds
  }

  async sendAuthenticatedMessage(message, userId) {
    const response = await fetch(this.agentEndpoint, {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({
        jsonrpc: "2.0",
        id: crypto.randomUUID(),
        method: "message/send",
        params: {
          message: {
            messageId: crypto.randomUUID(),
            role: "user",
            parts: [{text: message}]
          }
        },
        user_id: userId // Use stored OAuth session
      })
    });

    if (!response.ok) {
      throw new Error(`Agent request failed: ${response.status}`);
    }

    return await response.json();
  }

  closeAuthModal() {
    const modal = document.querySelector('.oauth-modal');
    if (modal) {
      modal.parentElement.remove();
    }
  }
}

// Usage in web app
const agentClient = new AgentOAuthClient();
const result = await agentClient.sendMessage("Hello agent", "user@example.com");
```

#### **User Experience Flow:**
1. **User sends message** to agent via web app
2. **Web app detects** user needs authentication
3. **OAuth modal appears** with Google device flow instructions
4. **User completes OAuth** in new tab/window
5. **Web app polls** for completion automatically
6. **Message sent successfully** once authenticated
7. **Subsequent requests** use stored OAuth session

### 🔀 **Pattern C: Hybrid Approach (Best of Both Worlds)**

**Best for:** Web applications that want to support both authenticated and unauthenticated users seamlessly.

```javascript
class HybridAgentClient {
  constructor(authService, agentEndpoint = 'http://localhost:8001') {
    this.authService = authService;
    this.agentEndpoint = agentEndpoint;
    this.oauthClient = new AgentOAuthClient(agentEndpoint);
  }

  async sendMessage(message, userId = null) {
    // Strategy 1: Try bearer token if web app has authenticated user
    if (await this.authService.isUserLoggedIn()) {
      try {
        return await this.sendWithBearerToken(message);
      } catch (error) {
        console.log('Bearer token failed, falling back to OAuth', error);
      }
    }

    // Strategy 2: Fall back to OAuth device flow
    if (userId) {
      return await this.oauthClient.sendMessage(message, userId);
    }

    // Strategy 3: Prompt for user identification
    throw new Error('Authentication required. Please provide userId or log into the web app.');
  }

  async sendWithBearerToken(message) {
    const token = await this.authService.getCurrentUserToken();

    const response = await fetch(this.agentEndpoint, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        jsonrpc: "2.0",
        id: crypto.randomUUID(),
        method: "message/send",
        params: {
          message: {
            messageId: crypto.randomUUID(),
            role: "user",
            parts: [{text: message}]
          }
        }
      })
    });

    if (!response.ok) {
      throw new Error(`Bearer token authentication failed: ${response.status}`);
    }

    return await response.json();
  }
}

// Usage scenarios
const hybridClient = new HybridAgentClient(webAppAuthService);

// Scenario 1: Authenticated web app user (uses bearer token)
const result1 = await hybridClient.sendMessage("Hello from logged-in user");

// Scenario 2: Unauthenticated user (uses OAuth device flow)
const result2 = await hybridClient.sendMessage("Hello from guest", "guest@example.com");
```

## User Experience Scenarios

### 🎭 **Scenario 1: First-Time User (OAuth Device Flow)**

```
Timeline:
┌─────────────────────────────────────────────────────────────────┐
│ 1. User visits web app (not authenticated)                     │
│ 2. User sends message: "Analyze my data"                       │
│ 3. Web app → Agent: Request without auth                       │
│ 4. Agent → Web app: 401 with auth requirements                 │
│ 5. Web app initiates OAuth device flow                         │
│ 6. Modal appears: "Visit google.com/device, enter VJX-TVD"     │
│ 7. User completes OAuth in new tab                             │
│ 8. Web app polls and detects completion                        │
│ 9. Original message sent successfully                          │
│10. User gets response: "Analysis complete..."                  │
└─────────────────────────────────────────────────────────────────┘
```

### 🔐 **Scenario 2: Authenticated Web App User (Bearer Token)**

```
Timeline:
┌─────────────────────────────────────────────────────────────────┐
│ 1. User already logged into web app                            │
│ 2. User sends message: "Analyze my data"                       │
│ 3. Web app → Agent: Request with Bearer token                  │
│ 4. Agent validates JWT and processes immediately               │
│ 5. User gets response: "Analysis complete..."                  │
└─────────────────────────────────────────────────────────────────┘
```

### 🔄 **Scenario 3: Returning User (Stored OAuth Session)**

```
Timeline:
┌─────────────────────────────────────────────────────────────────┐
│ 1. User previously completed OAuth device flow                 │
│ 2. User sends message: "Analyze my data"                       │
│ 3. Web app → Agent: Request with user_id                       │
│ 4. Agent finds stored OAuth tokens                             │
│ 5. Request processed immediately                               │
│ 6. User gets response: "Analysis complete..."                  │
└─────────────────────────────────────────────────────────────────┘
```

## Error Handling and Edge Cases

### 🔧 **Robust Error Handling**

```javascript
class RobustAgentClient {
  async sendMessage(message, userId = null) {
    try {
      return await this.attemptRequest(message, userId);
    } catch (error) {
      return this.handleError(error, message, userId);
    }
  }

  async handleError(error, message, userId) {
    if (error.status === 401) {
      // Authentication required or expired
      if (userId) {
        console.log('Reauthenticating user...');
        await this.reauthenticateUser(userId);
        return await this.sendMessage(message, userId);
      } else {
        throw new Error('Authentication required. Please provide user identification.');
      }
    } else if (error.status === 403) {
      // Forbidden - user authenticated but not authorized
      throw new Error('Access denied. User may not have required permissions.');
    } else if (error.status >= 500) {
      // Server error - may be temporary
      console.log('Server error, retrying...');
      await this.delay(2000);
      return await this.attemptRequest(message, userId);
    } else {
      throw error;
    }
  }

  async reauthenticateUser(userId) {
    // Clear any cached authentication
    await this.clearUserAuth(userId);

    // Force new OAuth flow
    await this.authenticateUser(userId);
  }

  delay(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }
}
```

### 🚨 **Common Edge Cases**

| Scenario | Issue | Solution |
|----------|-------|----------|
| **Expired OAuth Token** | Stored session invalid | Automatic reauthentication |
| **Invalid Bearer Token** | JWT expired/malformed | Fallback to OAuth flow |
| **Network Failure** | Request timeout | Retry with exponential backoff |
| **Agent Offline** | Service unavailable | Queue requests, notify user |
| **Multiple Users** | Session conflicts | Separate auth per user ID |

## Backend Proxy Pattern (Recommended)

### 🛡️ **Secure Backend Integration**

For production web applications, consider proxying agent requests through your backend:

```javascript
// Frontend: Simplified client
class ProxiedAgentClient {
  async sendMessage(message) {
    // Send to your web app backend, not directly to agent
    const response = await fetch('/api/agent/message', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${this.webAppToken}` // Web app's own auth
      },
      body: JSON.stringify({ message })
    });

    return await response.json();
  }
}
```

```python
# Backend: Secure proxy (Python example)
from fastapi import FastAPI, Depends, HTTPException
from your_auth import get_current_user

app = FastAPI()

@app.post("/api/agent/message")
async def proxy_agent_message(
    request: MessageRequest,
    user = Depends(get_current_user)
):
    # Your backend handles authentication
    user_jwt = await create_jwt_for_user(user)

    # Forward to agent with proper authentication
    agent_response = await httpx.post(
        "https://agent.internal:8001/",
        headers={"Authorization": f"Bearer {user_jwt}"},
        json={
            "jsonrpc": "2.0",
            "id": str(uuid.uuid4()),
            "method": "message/send",
            "params": {"message": request.message}
        }
    )

    return agent_response.json()
```

**Benefits:**
- ✅ **Security**: Agent not exposed to frontend
- ✅ **Control**: Backend controls agent access
- ✅ **Monitoring**: Centralized logging and analytics
- ✅ **Scalability**: Backend can implement caching, rate limiting

## Configuration for Web Apps

### 🔧 **Agent Configuration**

```yaml
# config/oauth_config.yaml - Web app friendly settings
oauth:
  default_provider: "google"
  flow_type: "device_flow"  # Supports web app OAuth flows

  # Shorter session times for web apps
  token_storage:
    ttl_seconds: 7200  # 2 hours

environments:
  development:
    oauth:
      require_https: false  # Allow HTTP for local development

  production:
    oauth:
      require_https: true   # Force HTTPS for production

# CORS configuration for web apps
a2a:
  cors:
    allow_origins: ["https://yourdomain.com", "http://localhost:3000"]
    allow_methods: ["POST", "GET"]
    allow_headers: ["Authorization", "Content-Type"]
```

### 🌍 **CORS Setup**

```python
# In agent server setup
from starlette.middleware.cors import CORSMiddleware

middleware = [
    Middleware(
        CORSMiddleware,
        allow_origins=["https://yourdomain.com", "http://localhost:3000"],
        allow_credentials=True,
        allow_methods=["POST", "GET"],
        allow_headers=["Authorization", "Content-Type"],
    )
]
```

## Testing Web App Integration

### 🧪 **Testing OAuth Flow**

```html
<!DOCTYPE html>
<html>
<head>
    <title>Agent Integration Test</title>
</head>
<body>
    <div id="app">
        <h1>Agent Test</h1>
        <input type="text" id="message" placeholder="Enter message for agent">
        <input type="text" id="userId" placeholder="User ID (email)">
        <button onclick="sendMessage()">Send Message</button>
        <div id="result"></div>
    </div>

    <script>
        const agentClient = new AgentOAuthClient();

        async function sendMessage() {
            const message = document.getElementById('message').value;
            const userId = document.getElementById('userId').value;
            const resultDiv = document.getElementById('result');

            try {
                resultDiv.innerHTML = 'Sending message...';
                const result = await agentClient.sendMessage(message, userId);
                resultDiv.innerHTML = `<strong>Success:</strong> ${JSON.stringify(result, null, 2)}`;
            } catch (error) {
                resultDiv.innerHTML = `<strong>Error:</strong> ${error.message}`;
            }
        }
    </script>
</body>
</html>
```

### 🔄 **Testing Bearer Token Flow**

```javascript
// Mock web app authentication for testing
class MockWebAppAuth {
  constructor() {
    this.mockToken = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."; // Mock JWT
  }

  async isUserLoggedIn() {
    return true; // Simulate logged-in user
  }

  async getCurrentUserToken() {
    return this.mockToken;
  }
}

// Test bearer token integration
const mockAuth = new MockWebAppAuth();
const bearerClient = new AgentClient(mockAuth);

// This should work immediately without OAuth flow
bearerClient.sendMessage("Test message with bearer token")
  .then(result => console.log('Bearer token success:', result))
  .catch(error => console.error('Bearer token failed:', error));
```

## Best Practices

### ✅ **Recommendations**

1. **Use Bearer Tokens When Possible**
   - Seamless user experience
   - Leverages existing web app authentication
   - No additional user interaction required

2. **Implement OAuth Device Flow as Fallback**
   - Handles unauthenticated users gracefully
   - Provides path to authentication when needed
   - Stores sessions for returning users

3. **Proxy Through Backend (Production)**
   - Better security and control
   - Centralized logging and monitoring
   - Easier to implement rate limiting and caching

4. **Handle Errors Gracefully**
   - Clear error messages for users
   - Automatic retry for transient failures
   - Fallback authentication methods

5. **Optimize for Your Use Case**
   - Choose the integration pattern that fits your app architecture
   - Consider user authentication state and requirements
   - Balance security with user experience

### 🚫 **Common Pitfalls**

- **Don't expose agent directly** to frontend in production
- **Don't store OAuth tokens** in localStorage (use secure cookies)
- **Don't assume authentication state** - always verify
- **Don't ignore CORS** requirements for browser requests
- **Don't hardcode URLs** - make endpoints configurable

## Summary

The agent template provides flexible authentication that works well with web applications:

**🎯 Key Takeaways:**
- **Bearer Token Integration**: Best for authenticated web app users
- **OAuth Device Flow**: Works for unauthenticated users with clear UX
- **Hybrid Approach**: Combines both methods for maximum flexibility
- **Backend Proxy**: Recommended for production security

**🚀 Getting Started:**
1. Choose your integration pattern based on your web app's authentication
2. Implement error handling and fallback authentication
3. Test with both authenticated and unauthenticated users
4. Consider backend proxy for production deployments

The system is designed to work seamlessly with web applications while providing multiple authentication paths to ensure all users can access agent capabilities securely.