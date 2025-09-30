# Environment Configuration Examples

This document provides example environment configurations for different deployment scenarios.

## 📁 Configuration Files

- `minimal_remote_agents.yaml` - Single remote agent for simple scenarios
- `complete_remote_agents.yaml` - All available remote agents
- `development_remote_agents.yaml` - Development-optimized configuration
- `production_remote_agents.yaml` - Production-ready configuration

## 🔧 Environment Variables

### Development Environment

```bash
# Agent Configuration
export AGENT_NAME="AuthenticatedAgent"
export AGENT_PORT="8001"
export AGENT_HOST="localhost"
export MODEL_NAME="gemini-2.0-flash"

# Remote Agent Ports
export DATA_ANALYSIS_PORT="8002"
export NOTIFICATION_PORT="8003"
export APPROVAL_PORT="8004"

# Development Settings
export LOG_LEVEL="DEBUG"
export DEVELOPMENT_MODE="true"
export MOCK_EXTERNAL_SERVICES="true"

# Authentication (Development)
export OAUTH_CLIENT_ID="dev-client-id"
export OAUTH_CLIENT_SECRET="dev-client-secret"
export OAUTH_REDIRECT_URI="http://localhost:8001/auth/callback"

# Database (Development)
export DATABASE_URL="sqlite:///dev_agent.db"
```

### Testing Environment

```bash
# Agent Configuration
export AGENT_NAME="TestAgent"
export AGENT_PORT="8001"
export MODEL_NAME="gemini-2.0-flash"

# Test-specific Settings
export LOG_LEVEL="INFO"
export TEST_MODE="true"
export AUTO_APPROVE_WORKFLOWS="true"
export MOCK_PROVIDERS="true"

# Test Authentication
export OAUTH_CLIENT_ID="test-client-id"
export OAUTH_CLIENT_SECRET="test-client-secret"
export TEST_BEARER_TOKEN="test-token-12345"

# Remote Agents (Testing)
export DATA_ANALYSIS_PORT="8002"
export NOTIFICATION_PORT="8003"
export APPROVAL_PORT="8004"

# Test Database
export DATABASE_URL="sqlite:///:memory:"
```

### Staging Environment

```bash
# Agent Configuration
export AGENT_NAME="StagingAgent"
export AGENT_PORT="8001"
export AGENT_HOST="0.0.0.0"
export MODEL_NAME="gemini-2.0-flash"

# Staging Settings
export LOG_LEVEL="INFO"
export ENVIRONMENT="staging"
export SSL_ENABLED="true"

# Authentication (Staging)
export OAUTH_CLIENT_ID="staging-client-id"
export OAUTH_CLIENT_SECRET="staging-client-secret"
export OAUTH_REDIRECT_URI="https://staging.yourdomain.com/auth/callback"

# Remote Agents (Staging)
export DATA_ANALYSIS_URL="https://data-analysis-staging.yourdomain.com"
export NOTIFICATION_URL="https://notifications-staging.yourdomain.com"
export APPROVAL_URL="https://approvals-staging.yourdomain.com"

# Database (Staging)
export DATABASE_URL="postgresql://user:pass@staging-db:5432/agent_db"

# Monitoring
export METRICS_ENABLED="true"
export HEALTH_CHECK_INTERVAL="30"
```

### Production Environment

```bash
# Agent Configuration
export AGENT_NAME="ProductionAgent"
export AGENT_PORT="8001"
export AGENT_HOST="0.0.0.0"
export MODEL_NAME="gemini-2.0-flash"

# Production Settings
export LOG_LEVEL="WARN"
export ENVIRONMENT="production"
export SSL_ENABLED="true"
export SSL_CERT_PATH="/etc/ssl/certs/agent.crt"
export SSL_KEY_PATH="/etc/ssl/private/agent.key"

# Authentication (Production)
export OAUTH_CLIENT_ID="${OAUTH_CLIENT_ID}"  # From secrets manager
export OAUTH_CLIENT_SECRET="${OAUTH_CLIENT_SECRET}"  # From secrets manager
export OAUTH_REDIRECT_URI="https://agents.yourdomain.com/auth/callback"

# Remote Agents (Production)
export DATA_ANALYSIS_URL="https://data-analysis.yourdomain.com"
export NOTIFICATION_URL="https://notifications.yourdomain.com"
export APPROVAL_URL="https://approvals.yourdomain.com"

# Database (Production)
export DATABASE_URL="${DATABASE_URL}"  # From secrets manager

# Security
export CORS_ALLOWED_ORIGINS="https://yourdomain.com,https://admin.yourdomain.com"
export RATE_LIMIT_ENABLED="true"
export RATE_LIMIT_REQUESTS_PER_MINUTE="100"

# Monitoring and Observability
export METRICS_ENABLED="true"
export TRACING_ENABLED="true"
export HEALTH_CHECK_INTERVAL="60"
export PROMETHEUS_ENDPOINT="/metrics"
export JAEGER_ENDPOINT="http://jaeger:14268/api/traces"

# Performance
export WORKER_PROCESSES="4"
export MAX_CONNECTIONS="1000"
export REQUEST_TIMEOUT="30"
export KEEP_ALIVE_TIMEOUT="5"
```

## 🐳 Docker Environment Files

### Development (.env.development)

```env
# Agent Configuration
AGENT_NAME=DevAgent
AGENT_PORT=8001
MODEL_NAME=gemini-2.0-flash

# Development flags
LOG_LEVEL=DEBUG
DEVELOPMENT_MODE=true
MOCK_EXTERNAL_SERVICES=true

# Authentication
OAUTH_CLIENT_ID=dev-client-id
OAUTH_CLIENT_SECRET=dev-client-secret

# Remote agent ports
DATA_ANALYSIS_PORT=8002
NOTIFICATION_PORT=8003
APPROVAL_PORT=8004
```

### Production (.env.production)

```env
# Agent Configuration
AGENT_NAME=ProductionAgent
AGENT_PORT=8001
MODEL_NAME=gemini-2.0-flash

# Production flags
LOG_LEVEL=WARN
ENVIRONMENT=production
SSL_ENABLED=true

# Remote agent URLs (use Docker service names)
DATA_ANALYSIS_URL=https://data-analysis-service:8002
NOTIFICATION_URL=https://notification-service:8003
APPROVAL_URL=https://approval-service:8004

# Security
CORS_ALLOWED_ORIGINS=https://yourdomain.com
RATE_LIMIT_ENABLED=true

# Performance
WORKER_PROCESSES=4
MAX_CONNECTIONS=1000
```

## ☸️ Kubernetes ConfigMaps

### Development ConfigMap

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: agent-dev-config
data:
  AGENT_NAME: "DevAgent"
  AGENT_PORT: "8001"
  LOG_LEVEL: "DEBUG"
  DEVELOPMENT_MODE: "true"
  MODEL_NAME: "gemini-2.0-flash"

  # Remote agent URLs
  DATA_ANALYSIS_URL: "http://data-analysis-service:8002"
  NOTIFICATION_URL: "http://notification-service:8003"
  APPROVAL_URL: "http://approval-service:8004"
```

### Production ConfigMap

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: agent-prod-config
data:
  AGENT_NAME: "ProductionAgent"
  AGENT_PORT: "8001"
  LOG_LEVEL: "WARN"
  ENVIRONMENT: "production"
  MODEL_NAME: "gemini-2.0-flash"

  # Remote agent URLs
  DATA_ANALYSIS_URL: "https://data-analysis.yourdomain.com"
  NOTIFICATION_URL: "https://notifications.yourdomain.com"
  APPROVAL_URL: "https://approvals.yourdomain.com"

  # Security settings
  CORS_ALLOWED_ORIGINS: "https://yourdomain.com"
  RATE_LIMIT_ENABLED: "true"
  SSL_ENABLED: "true"
```

## 🔒 Secrets Management

### Kubernetes Secrets

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: agent-secrets
type: Opaque
data:
  OAUTH_CLIENT_ID: <base64-encoded-client-id>
  OAUTH_CLIENT_SECRET: <base64-encoded-client-secret>
  DATABASE_URL: <base64-encoded-database-url>
  JWT_SECRET_KEY: <base64-encoded-jwt-secret>
```

### Docker Secrets

```bash
# Create secrets
echo "your-oauth-client-id" | docker secret create oauth_client_id -
echo "your-oauth-client-secret" | docker secret create oauth_client_secret -
echo "your-database-url" | docker secret create database_url -
```

### Environment-specific Secrets

#### Development
```bash
# Use local files or environment variables
export OAUTH_CLIENT_ID="dev-client-id"
export OAUTH_CLIENT_SECRET="dev-client-secret"
```

#### Production
```bash
# Use secrets management service
export OAUTH_CLIENT_ID=$(aws secretsmanager get-secret-value --secret-id oauth-client-id --query SecretString --output text)
export OAUTH_CLIENT_SECRET=$(aws secretsmanager get-secret-value --secret-id oauth-client-secret --query SecretString --output text)
```

## 📋 Configuration Templates

### Makefile for Environment Management

```makefile
# Set environment-specific variables
.PHONY: dev staging prod

dev:
	@echo "Setting up development environment..."
	@cp examples/configurations/development_remote_agents.yaml config/remote_agents.yaml
	@export $(shell cat .env.development | xargs)
	@echo "Development environment ready"

staging:
	@echo "Setting up staging environment..."
	@cp examples/configurations/complete_remote_agents.yaml config/remote_agents.yaml
	@export $(shell cat .env.staging | xargs)
	@echo "Staging environment ready"

prod:
	@echo "Setting up production environment..."
	@cp examples/configurations/production_remote_agents.yaml config/remote_agents.yaml
	@export $(shell cat .env.production | xargs)
	@echo "Production environment ready"

test:
	@echo "Setting up test environment..."
	@cp examples/configurations/minimal_remote_agents.yaml config/remote_agents.yaml
	@export $(shell cat .env.test | xargs)
	@python -m pytest testing/
```

### Environment Setup Script

```bash
#!/bin/bash
# setup_environment.sh

set -e

ENVIRONMENT=${1:-development}

echo "Setting up $ENVIRONMENT environment..."

case $ENVIRONMENT in
  development)
    cp examples/configurations/development_remote_agents.yaml config/remote_agents.yaml
    export $(cat .env.development | xargs)
    echo "Development environment configured"
    ;;
  staging)
    cp examples/configurations/complete_remote_agents.yaml config/remote_agents.yaml
    export $(cat .env.staging | xargs)
    echo "Staging environment configured"
    ;;
  production)
    cp examples/configurations/production_remote_agents.yaml config/remote_agents.yaml
    export $(cat .env.production | xargs)
    echo "Production environment configured"
    ;;
  *)
    echo "Unknown environment: $ENVIRONMENT"
    echo "Usage: $0 [development|staging|production]"
    exit 1
    ;;
esac

echo "Environment setup complete for: $ENVIRONMENT"
```

## 🧪 Testing Configuration

### Test Configuration Validation

```python
# test_config_validation.py
import yaml
import pytest
from pathlib import Path

def test_configuration_files():
    """Test that all configuration files are valid YAML."""
    config_dir = Path("examples/configurations")

    for config_file in config_dir.glob("*.yaml"):
        with open(config_file) as f:
            try:
                config = yaml.safe_load(f)
                assert config is not None
                print(f"✅ {config_file.name} is valid")
            except yaml.YAMLError as e:
                pytest.fail(f"❌ {config_file.name} has invalid YAML: {e}")

def test_remote_agents_schema():
    """Test that remote agent configurations have required fields."""
    config_files = [
        "examples/configurations/complete_remote_agents.yaml",
        "examples/configurations/minimal_remote_agents.yaml"
    ]

    required_fields = ["name", "description", "agent_card_url", "enabled"]

    for config_file in config_files:
        with open(config_file) as f:
            config = yaml.safe_load(f)

        if "remote_agents" in config:
            for agent in config["remote_agents"]:
                for field in required_fields:
                    assert field in agent, f"Missing {field} in {config_file}"

        print(f"✅ {config_file} has valid schema")
```

Run configuration tests:
```bash
python -m pytest test_config_validation.py -v
```