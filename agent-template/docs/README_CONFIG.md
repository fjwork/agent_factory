# Configuration Directory Documentation

This directory (agent-template/config) contains all configuration files for the ADK agent template. These YAML files define agent behavior, authentication settings, deployment configurations, and multi-agent orchestration.

## Configuration Architecture

```
config/
├── agent_config.yaml       # Core agent settings and capabilities
├── oauth_config.yaml       # Authentication and OAuth providers
├── deployment_config.yaml  # Deployment and infrastructure settings
└── remote_agents.yaml      # Multi-agent orchestration (optional)
```

The configuration system supports:
- **Environment-specific overrides** (development/staging/production)
- **Environment variable expansion** (`${VAR:default}` syntax)
- **Hierarchical configuration merging**
- **Secure credential management**

## Configuration Files

### `agent_config.yaml`
**Purpose**: Core agent metadata, capabilities, and behavior settings

**Key Sections:**
```yaml
agent:
  name: "${AGENT_NAME:AuthenticatedAgent}"
  version: "${AGENT_VERSION:1.0.0}"
  description: "Agent description"

model:
  provider: "${MODEL_PROVIDER:gemini}"
  name: "${MODEL_NAME:gemini-2.0-flash}"
  use_vertex_ai: true

capabilities:
  streaming: true
  push_notifications: false
  authenticated_extended_card: true

skills:
  - id: "authenticated_operations"
    name: "Authenticated Operations"
    description: "OAuth-enabled operations"
    examples: ["Access my data", "Show my profile"]
```

**Configuration Targets:**
- Agent metadata and versioning
- Model selection and configuration
- Agent capabilities and features
- Skill definitions and examples
- A2A server settings (host, port, transport)
- Environment-specific behavior overrides

**Environment Variables:**
- `AGENT_NAME` - Agent display name
- `AGENT_VERSION` - Agent version
- `MODEL_NAME` - Gemini model to use
- `A2A_HOST` - Server binding host
- `A2A_PORT` - Server port (default: 8000)

### `oauth_config.yaml`
**Purpose**: Authentication providers, security settings, and OAuth flow configuration

**Key Sections:**
```yaml
oauth:
  default_provider: "google"
  flow_type: "device_flow"
  scopes: "openid profile email"

  token_storage:
    type: "file"  # memory|file|secret_manager
    encryption: true
    ttl_seconds: 3600

  security:
    validate_issuer: true
    validate_audience: true
    require_https: true

providers:
  google:
    client_id: "${GOOGLE_OAUTH_CLIENT_ID}"
    client_secret: "${GOOGLE_OAUTH_CLIENT_SECRET}"
    # ... endpoints and scopes

a2a_auth:
  security_schemes:
    oauth2: # OAuth 2.0 flow definition
    bearerAuth: # Bearer token definition
    apiKey: # API key definition
```

**Supported Providers:**
- **Google** - Google OAuth 2.0 (default)
- **Azure** - Azure AD/Microsoft Graph
- **Okta** - Okta Identity
- **Custom** - Generic OAuth 2.0 provider

**OAuth Flow Types:**
- **device_flow** - Best for CLI/headless environments
- **authorization_code** - Best for web applications
- **client_credentials** - Best for service accounts

**Token Storage Options:**
- **memory** - In-memory (development only)
- **file** - Encrypted file storage
- **secret_manager** - Google Cloud Secret Manager

**Environment Variables:**
- `GOOGLE_OAUTH_CLIENT_ID` - Google OAuth client ID (required)
- `GOOGLE_OAUTH_CLIENT_SECRET` - Google OAuth client secret (required)
- `AZURE_OAUTH_CLIENT_ID` - Azure AD client ID (optional)
- `AZURE_OAUTH_CLIENT_SECRET` - Azure AD client secret (optional)
- `AZURE_TENANT_ID` - Azure AD tenant ID (optional)
- `TOKEN_STORAGE_TYPE` - Storage backend selection
- `OAUTH_REQUIRE_HTTPS` - HTTPS enforcement

### `deployment_config.yaml`
**Purpose**: Infrastructure deployment, platform settings, and CI/CD configuration

**Key Sections:**
```yaml
deployment:
  image:
    registry: "gcr.io"
    project_id: "${GOOGLE_CLOUD_PROJECT}"
    name: "adk-agent"
    tag: "latest"

  env_vars:
    # Runtime environment variables
    GOOGLE_CLOUD_PROJECT: "${GOOGLE_CLOUD_PROJECT}"
    AGENT_NAME: "${AGENT_NAME:MyAgent}"
    MODEL_NAME: "${MODEL_NAME:gemini-2.0-flash}"

  secrets:
    # Secret Manager references
    GOOGLE_OAUTH_CLIENT_ID: "oauth-client-id"
    GOOGLE_OAUTH_CLIENT_SECRET: "oauth-client-secret"

cloud_run:
  service_name: "${CLOUD_RUN_SERVICE_NAME:adk-agent}"
  region: "us-central1"

  resources:
    cpu: "1"
    memory: "512Mi"
    max_instances: 10

agent_engine:
  display_name: "${AGENT_ENGINE_DISPLAY_NAME:MyAgent}"
  model: "projects/.../models/gemini-2.0-flash"
  temperature: 0.7

docker:
  base_image: "python:3.11-slim"
  build:
    context: "."
    dockerfile: "deployment/docker/Dockerfile"
```

**Deployment Targets:**
- **Cloud Run** - Google Cloud Run serverless containers
- **Agent Engine** - Vertex AI Agent Engine (managed)
- **Docker** - Containerized deployment
- **Local** - Development environment

**Environment-Specific Overrides:**
Each deployment target supports development/staging/production overrides for:
- Resource allocation (CPU, memory, instances)
- Security settings (authentication, HTTPS)
- Logging levels and monitoring
- Feature flags and capabilities

**Environment Variables:**
- `GOOGLE_CLOUD_PROJECT` - GCP project ID (required)
- `GOOGLE_CLOUD_LOCATION` - GCP region (default: us-central1)
- `CLOUD_RUN_SERVICE_NAME` - Cloud Run service name
- `IMAGE_NAME` - Docker image name
- `IMAGE_TAG` - Docker image tag

### `remote_agents.yaml`
**Purpose**: Multi-agent orchestration configuration (optional)

**Key Structure:**
```yaml
remote_agents:
  - name: "auth_validation_agent"
    description: "Authentication testing agent"
    agent_card_url: "http://localhost:8002"
    enabled: true

  - name: "data_analysis_agent"
    description: "Data analysis and reporting"
    agent_card_url: "http://localhost:8003"
    enabled: false  # Disabled by default
```

**Configuration Behavior:**
- **File Missing/Empty**: Agent runs in **standalone mode**
- **File Present**: Agent runs in **multi-agent orchestration mode**
- **enabled: false**: Individual agents can be disabled without removing config

**Agent Requirements:**
Each remote agent must:
1. **Be accessible** at the specified `agent_card_url`
2. **Expose agent card** at `/.well-known/agent-card.json`
3. **Support A2A protocol** for task delegation
4. **Handle authentication forwarding** (bearer tokens, OAuth context)

**Default Configuration:**
- Single `auth_validation_agent` for testing authentication forwarding
- Additional agents commented out (data analysis, notifications)
- Port allocation: 8001 (root), 8002+ (remote agents)

## Environment Management

### Environment Variable Expansion
All configuration files support `${VAR:default}` syntax:

```yaml
# Required variable (fails if not set)
client_id: "${GOOGLE_OAUTH_CLIENT_ID}"

# Optional with default
log_level: "${LOG_LEVEL:INFO}"

# Nested variable expansion
service_name: "${CLOUD_RUN_SERVICE_NAME:${AGENT_NAME:adk-agent}}"
```

### Environment-Specific Overrides
Each file supports `environments` section for environment-specific settings:

```yaml
# Base configuration
oauth:
  require_https: true
  log_level: "INFO"

# Environment overrides
environments:
  development:
    oauth:
      require_https: false
      log_level: "DEBUG"

  production:
    oauth:
      require_https: true
      log_level: "WARNING"
```

**Environment Selection:**
- Set via `ENVIRONMENT` environment variable
- Defaults to `development`
- Supported values: `development`, `staging`, `production`

### Configuration Loading Order
1. **Base configuration** from main sections
2. **Environment-specific overrides** from `environments` section
3. **Environment variable expansion** (`${VAR:default}`)
4. **Runtime validation** and error checking

## Required Environment Variables

### Minimal Setup (Development)
```bash
# OAuth credentials (required)
export GOOGLE_OAUTH_CLIENT_ID="your-google-client-id"
export GOOGLE_OAUTH_CLIENT_SECRET="your-google-client-secret"

# Google Cloud project (required for some features)
export GOOGLE_CLOUD_PROJECT="your-project-id"

# Environment
export ENVIRONMENT="development"
```

### Production Setup
```bash
# OAuth credentials (store in Secret Manager)
export GOOGLE_OAUTH_CLIENT_ID="your-google-client-id"
export GOOGLE_OAUTH_CLIENT_SECRET="your-google-client-secret"

# Cloud infrastructure
export GOOGLE_CLOUD_PROJECT="your-project-id"
export GOOGLE_CLOUD_LOCATION="us-central1"

# Agent configuration
export AGENT_NAME="MyProductionAgent"
export AGENT_VERSION="1.0.0"

# Security
export TOKEN_STORAGE_TYPE="secret_manager"
export OAUTH_REQUIRE_HTTPS="true"

# Environment
export ENVIRONMENT="production"
```

### Multi-Agent Setup
```bash
# All of the above, plus:

# Remote agent endpoints
export REMOTE_AGENT_BASE_URL="https://remote-agents.example.com"

# Port allocation
export A2A_PORT="8001"  # Root agent
# Remote agents typically run on 8002, 8003, 8004, etc.
```

## Configuration Validation

### OAuth Configuration Validation
The system validates:
- **Required credentials** are present for enabled providers
- **Endpoint URLs** are valid and accessible
- **Scopes** are properly formatted
- **Flow types** are supported
- **Security settings** are appropriate for environment

### Agent Configuration Validation
The system validates:
- **Model names** are valid and accessible
- **Capabilities** are correctly configured
- **Skills** have required fields (id, name, description)
- **A2A settings** are valid (host, port, transport)

### Deployment Configuration Validation
The system validates:
- **Required environment variables** are present
- **Resource allocations** are within platform limits
- **Secret references** exist in Secret Manager
- **Image configurations** are valid

### Remote Agents Validation
The system validates:
- **Agent card URLs** are accessible
- **Agent cards** are valid JSON with required fields
- **A2A endpoints** respond correctly
- **Authentication forwarding** works as expected

## Configuration Best Practices

### Development
```yaml
# Use memory storage for faster development
oauth:
  token_storage:
    type: "memory"

# Disable HTTPS for local testing
oauth:
  security:
    require_https: false

# Enable debug logging
deployment:
  env_vars:
    LOG_LEVEL: "DEBUG"

# Use minimal resources
cloud_run:
  resources:
    cpu: "0.5"
    memory: "256Mi"
```

### Production
```yaml
# Use Secret Manager for secure storage
oauth:
  token_storage:
    type: "secret_manager"

# Enforce HTTPS
oauth:
  security:
    require_https: true
    validate_issuer: true
    validate_audience: true

# Production logging
deployment:
  env_vars:
    LOG_LEVEL: "WARNING"

# Appropriate resources
cloud_run:
  resources:
    cpu: "2"
    memory: "1Gi"
    max_instances: 20
    min_instances: 1
```

### Multi-Agent
```yaml
# Enable remote agents
remote_agents:
  - name: "data_analysis_agent"
    description: "Data analysis and reporting"
    agent_card_url: "https://data-agent.example.com"
    enabled: true

# Ensure authentication forwarding
oauth:
  token_storage:
    type: "secret_manager"  # Shared storage for multi-agent

# Production-grade security
oauth:
  security:
    require_https: true
    validate_issuer: true
```

## Configuration Templates

### Minimal Development Template
```yaml
# agent_config.yaml (minimal)
agent:
  name: "DevAgent"
  model:
    name: "gemini-2.0-flash"

# oauth_config.yaml (minimal)
oauth:
  default_provider: "google"
  flow_type: "device_flow"

providers:
  google:
    client_id: "${GOOGLE_OAUTH_CLIENT_ID}"
    client_secret: "${GOOGLE_OAUTH_CLIENT_SECRET}"

# No deployment_config.yaml needed for local development
# No remote_agents.yaml for standalone mode
```

### Production Multi-Agent Template
All configuration files fully populated with:
- Complete OAuth provider configurations
- Production deployment settings
- Multi-agent orchestration
- Security hardening
- Monitoring and logging
- CI/CD integration

## Troubleshooting

### Common Configuration Issues

#### "Provider not found" Error
```bash
# Check OAuth configuration
cat config/oauth_config.yaml | grep -A 10 "providers:"

# Verify environment variables
echo $GOOGLE_OAUTH_CLIENT_ID
echo $GOOGLE_OAUTH_CLIENT_SECRET
```

#### "Remote agent not accessible" Error
```bash
# Check remote agent configuration
cat config/remote_agents.yaml

# Test agent card accessibility
curl http://localhost:8002/.well-known/agent-card.json
```

#### "Authentication required" Error
```bash
# Check OAuth configuration
cat config/oauth_config.yaml | grep -A 5 "oauth:"

# Verify token storage configuration
echo $TOKEN_STORAGE_TYPE
```

### Configuration Debugging
```bash
# Enable debug logging
export LOG_LEVEL="DEBUG"

# Validate configuration loading
python -c "
from auth.auth_config import load_auth_config
config = load_auth_config()
print(f'Loaded config: {config.default_provider}')
print(f'Providers: {list(config.providers.keys())}')
"

# Test environment variable expansion
python -c "
import yaml
from auth.auth_config import ConfigLoader
loader = ConfigLoader()
with open('config/oauth_config.yaml') as f:
    raw = yaml.safe_load(f)
expanded = loader._expand_env_vars(raw)
print(expanded)
"
```

## Security Considerations

### Credential Management
- **Never commit credentials** to version control
- **Use environment variables** for all sensitive data
- **Use Secret Manager** for production deployments
- **Rotate credentials** regularly

### Configuration Security
- **Validate all inputs** during configuration loading
- **Use HTTPS** for all OAuth endpoints in production
- **Enable issuer validation** for JWT tokens
- **Audit configuration changes** in production

### Multi-Agent Security
- **Authenticate all A2A calls** between agents
- **Validate agent cards** before adding to configuration
- **Use TLS** for inter-agent communication in production
- **Isolate agent authentication contexts**

---

## Configuration Migration

### Upgrading from v1.0 to v2.0
1. **Backup existing configuration** files
2. **Update YAML structure** for new features
3. **Add missing environment variables**
4. **Test configuration loading** in development
5. **Deploy to staging** before production

### Environment Migration
1. **Export current configuration** from development
2. **Update environment variables** for target environment
3. **Validate OAuth provider** accessibility in target
4. **Test authentication flows** end-to-end
5. **Monitor configuration** after deployment

This configuration system provides flexible, secure, and environment-aware configuration management for all aspects of the ADK agent template, from basic authentication to complex multi-agent orchestration.