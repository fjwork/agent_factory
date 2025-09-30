# Profile Agent Setup Guide

This guide walks you through setting up and testing the Profile Agent using our standardized ADK agent pattern.

## 🚀 Quick Setup Steps

### 1. Environment Setup
```bash
cd agents/profile-agent
cp .env.example .env
# Edit .env with your OAuth credentials
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure OAuth Credentials

#### Google OAuth Setup:
1. Go to [Google Cloud Console](https://console.cloud.google.com/apis/credentials)
2. Create OAuth 2.0 Client ID for "Desktop application"
3. Copy Client ID and Secret to your `.env` file:

```bash
GOOGLE_OAUTH_CLIENT_ID=your-client-id-here
GOOGLE_OAUTH_CLIENT_SECRET=your-client-secret-here
```

### 4. Start the Agent
```bash
python src/agent.py
```

The agent will start on `http://localhost:8001`

## 🧪 Testing the Agent

### 1. Check Agent Health
```bash
curl http://localhost:8001/health
```

### 2. View Agent Card
```bash
curl http://localhost:8001/.well-known/agent-card.json
```

### 3. Test OAuth Authentication

#### Step 1: Initiate Authentication
```bash
curl -X POST http://localhost:8001/auth/initiate \
  -H "Content-Type: application/json" \
  -d '{"user_id": "test-user", "provider": "google"}'
```

Response will include:
- `verification_url`: URL to visit for authentication
- `user_code`: Code to enter
- `session_id`: For completing authentication

#### Step 2: Complete Authentication (after visiting URL)
```bash
curl -X POST http://localhost:8001/auth/complete \
  -H "Content-Type: application/json" \
  -d '{"session_id": "your-session-id-from-step-1"}'
```

#### Step 3: Check Authentication Status
```bash
curl "http://localhost:8001/auth/status?user_id=test-user"
```

### 4. Test Profile Retrieval

#### Get Full Profile
```bash
curl -X POST http://localhost:8001/ \
  -H "Content-Type: application/json" \
  -H "X-User-ID: test-user" \
  -d '{
    "message": "What is my profile?",
    "user_id": "test-user"
  }'
```

#### Get Profile Summary
```bash
curl -X POST http://localhost:8001/ \
  -H "Content-Type: application/json" \
  -H "X-User-ID: test-user" \
  -d '{
    "message": "Give me a friendly summary of my profile",
    "user_id": "test-user"
  }'
```

## 📋 Agent Skills

The Profile Agent supports these skills (defined in `config/agent_config.yaml`):

### 1. User Profile Access
- **ID**: `user_profile_access`
- **Examples**:
  - "What is my profile?"
  - "Show me my profile information"
  - "Get my user details"
  - "What's my email address?"

### 2. Profile Summary
- **ID**: `profile_summary`
- **Examples**:
  - "Give me a summary of my account"
  - "Tell me about myself"
  - "What information do you have about me?"

## 🔧 Customization

### Adding New Profile Tools

1. Create new tool in `src/tools/`:
```python
class MyCustomProfileTool(AuthenticatedTool):
    async def execute_authenticated(self, user_context, **kwargs):
        # Your implementation
        pass
```

2. Register in `src/agent.py`:
```python
custom_tool = MyCustomProfileTool()
custom_function_tool = FunctionTool(custom_tool.execute_authenticated)
# Add to tools list
```

3. Update skills in `config/agent_config.yaml`

### Environment Configuration

- **Development**: Uses `localhost`, debug logging, CORS enabled
- **Staging**: Production-like with info logging
- **Production**: Secure settings, warning-level logging

## 🚨 Troubleshooting

### Common Issues:

1. **OAuth Setup**: Ensure credentials are correctly set in `.env`
2. **Port Conflicts**: Change `A2A_PORT` if 8001 is in use
3. **Dependencies**: Run `pip install -r requirements.txt`
4. **Google Cloud**: Ensure project is set up correctly

### Debug Mode:
Set `LOG_LEVEL=DEBUG` in `.env` for detailed logging.

## 🔐 Security Notes

- Tokens are stored in memory by default (development)
- Use Secret Manager for production (`TOKEN_STORAGE_TYPE=secret_manager`)
- HTTPS is disabled for development (`OAUTH_REQUIRE_HTTPS=false`)
- Always use HTTPS in production environments