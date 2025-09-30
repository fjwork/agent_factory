# Setup Guide

This guide walks you through setting up the ADK Agent Template with OAuth authentication.

## Prerequisites

Before you begin, ensure you have:

- Python 3.11 or later
- Google Cloud CLI (`gcloud`) installed and configured
- Docker (optional, for local development)
- A Google Cloud Project with billing enabled

## Step 1: Initial Setup

### Automated Setup

Run the automated setup script:

```bash
# Basic setup
./deployment/scripts/setup.sh

# Development setup with additional dependencies
./deployment/scripts/setup.sh --dev

# Specify project and location
./deployment/scripts/setup.sh --project YOUR_PROJECT_ID --location us-central1
```

### Manual Setup

If you prefer manual setup:

1. **Authenticate with Google Cloud:**
   ```bash
   gcloud auth login
   gcloud auth application-default login
   ```

2. **Set your project:**
   ```bash
   export GOOGLE_CLOUD_PROJECT=your-project-id
   gcloud config set project $GOOGLE_CLOUD_PROJECT
   ```

3. **Enable required APIs:**
   ```bash
   gcloud services enable aiplatform.googleapis.com
   gcloud services enable run.googleapis.com
   gcloud services enable artifactregistry.googleapis.com
   gcloud services enable secretmanager.googleapis.com
   gcloud services enable cloudbuild.googleapis.com
   ```

## Step 2: OAuth Configuration

### Google OAuth Setup

1. **Go to Google Cloud Console:**
   - Navigate to [APIs & Services > Credentials](https://console.cloud.google.com/apis/credentials)

2. **Create OAuth 2.0 Client ID:**
   - Click "Create Credentials" > "OAuth 2.0 Client ID"
   - Select "Desktop application" as the application type
   - Name it "ADK Agent OAuth Client"
   - Download the client configuration

3. **Store credentials securely:**

   **Option A: Environment Variables**
   ```bash
   export GOOGLE_OAUTH_CLIENT_ID="your-client-id"
   export GOOGLE_OAUTH_CLIENT_SECRET="your-client-secret"
   ```

   **Option B: Secret Manager (Recommended for production)**
   ```bash
   # Create secrets
   gcloud secrets create oauth-client-id --replication-policy="automatic"
   gcloud secrets create oauth-client-secret --replication-policy="automatic"

   # Add secret values
   echo -n "your-client-id" | gcloud secrets versions add oauth-client-id --data-file=-
   echo -n "your-client-secret" | gcloud secrets versions add oauth-client-secret --data-file=-
   ```

### Azure OAuth Setup (Optional)

If you want to support Azure authentication:

1. **Register an application in Azure AD:**
   - Go to [Azure Portal > App registrations](https://portal.azure.com/#blade/Microsoft_AAD_RegisteredApps)
   - Click "New registration"
   - Set redirect URI to `http://localhost` for desktop apps

2. **Configure credentials:**
   ```bash
   export AZURE_OAUTH_CLIENT_ID="your-azure-client-id"
   export AZURE_OAUTH_CLIENT_SECRET="your-azure-client-secret"
   export AZURE_TENANT_ID="your-azure-tenant-id"
   ```

### Okta OAuth Setup (Optional)

If you want to support Okta authentication:

1. **Create an application in Okta:**
   - Go to your Okta Admin Console > Applications
   - Create a new "Native" application
   - Note the Client ID and configure redirect URIs

2. **Configure credentials:**
   ```bash
   export OKTA_OAUTH_CLIENT_ID="your-okta-client-id"
   export OKTA_OAUTH_CLIENT_SECRET="your-okta-client-secret"
   export OKTA_DOMAIN="your-okta-domain.okta.com"
   ```

## Step 3: Configuration

### Environment Configuration

1. **Copy the example environment file:**
   ```bash
   cp .env.example .env
   ```

2. **Edit `.env` with your settings:**
   ```bash
   # Required settings
   GOOGLE_CLOUD_PROJECT=your-project-id
   GOOGLE_OAUTH_CLIENT_ID=your-client-id
   GOOGLE_OAUTH_CLIENT_SECRET=your-client-secret

   # Agent settings
   AGENT_NAME=MyCustomAgent
   AGENT_VERSION=1.0.0

   # OAuth settings
   OAUTH_FLOW_TYPE=device_flow  # or authorization_code
   TOKEN_STORAGE_TYPE=secret_manager  # or memory, file
   ```

### Agent Configuration

Customize `config/agent_config.yaml`:

```yaml
agent:
  name: "${AGENT_NAME:MyCustomAgent}"
  description: "My custom agent with OAuth authentication"

  model:
    name: "gemini-2.0-flash"

skills:
  - id: "custom_skill"
    name: "Custom Skill"
    description: "My custom agent skill"
    tags: ["custom", "api"]
    examples:
      - "Can you help me with my custom task?"
```

### OAuth Provider Configuration

Edit `config/oauth_config.yaml` to customize OAuth settings:

```yaml
oauth:
  default_provider: "google"
  flow_type: "device_flow"
  scopes: "openid profile email"

  token_storage:
    type: "secret_manager"
    encryption: true
    ttl_seconds: 3600
```

## Step 4: Development Testing

### Install Dependencies

```bash
pip install -r requirements.txt

# For development
pip install -r requirements-dev.txt
```

### Run Locally

```bash
python src/agent.py
```

The agent will start on `http://localhost:8000` with the following endpoints:

- `GET /.well-known/agent-card.json` - Agent card
- `GET /health` - Health check
- `POST /auth/initiate` - Start OAuth flow
- `GET /auth/status` - Check authentication status

### Test Authentication

1. **Initiate OAuth flow:**
   ```bash
   curl -X POST http://localhost:8000/auth/initiate \
     -H "Content-Type: application/json" \
     -d '{"user_id": "test-user", "provider": "google"}'
   ```

2. **Follow the provided URL and enter the code**

3. **Check authentication status:**
   ```bash
   curl "http://localhost:8000/auth/status?user_id=test-user"
   ```

4. **Test agent interaction:**
   ```bash
   curl -X POST http://localhost:8000/ \
     -H "Content-Type: application/json" \
     -d '{"user_id": "test-user", "message": "Hello!"}'
   ```

## Step 5: Deployment

### Deploy to Cloud Run

```bash
# Development deployment
python deployment/cloud_run/deploy.py --environment development

# Production deployment
python deployment/cloud_run/deploy.py --environment production
```

### Deploy to Agent Engine

```bash
# Create new agent
python deployment/agent_engine/deploy.py --action create --environment production

# Test deployed agent
python deployment/agent_engine/deploy.py --action test --resource-id AGENT_ID
```

## Troubleshooting

### Common Issues

1. **Authentication Failed:**
   - Verify OAuth credentials are correct
   - Check that redirect URIs match your configuration
   - Ensure required scopes are included

2. **API Permissions:**
   - Verify all required APIs are enabled
   - Check IAM permissions for service accounts

3. **Token Storage:**
   - For Secret Manager: ensure proper IAM permissions
   - For file storage: check directory permissions
   - For memory storage: tokens are lost on restart

4. **Deployment Issues:**
   - Check Docker image build logs
   - Verify environment variables are set correctly
   - Review Cloud Run or Agent Engine logs

### Debug Logging

Enable debug logging:

```bash
export LOG_LEVEL=DEBUG
python src/agent.py
```

### Testing OAuth Flows

Test different OAuth flows:

```bash
# Device flow (recommended for CLI)
curl -X POST http://localhost:8000/auth/initiate \
  -d '{"user_id": "test", "provider": "google", "flow": "device_flow"}'

# Authorization code flow (for web apps)
curl -X POST http://localhost:8000/auth/initiate \
  -d '{"user_id": "test", "provider": "google", "flow": "authorization_code"}'
```

## Next Steps

1. **Customize your agent** by editing `src/agent.py`
2. **Add custom tools** using the `AuthenticatedTool` base class
3. **Configure additional OAuth providers** in `config/oauth_config.yaml`
4. **Set up monitoring** using Google Cloud Monitoring
5. **Deploy to production** with proper security settings

## Security Considerations

1. **Never commit secrets** to version control
2. **Use Secret Manager** for production deployments
3. **Enable HTTPS** in production environments
4. **Regularly rotate** OAuth client secrets
5. **Monitor access logs** for suspicious activity
6. **Use least privilege** IAM permissions

For more detailed information, see the other documentation files in the `docs/` directory.