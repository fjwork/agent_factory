# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

This is an **Agent Factory** - a comprehensive toolkit for creating Google ADK (Agent Development Kit) agents with OAuth authentication and Agent-to-Agent (A2A) protocol support. The repository uses a template-based approach for creating new agents with standardized authentication and communication patterns.

## Key Directory Structure

- `agent-template/` - Production-ready template for new ADK agents with OAuth + A2A
- `agents/` - Live agent instances created from the template
- `docs/` - Documentation and configuration templates
- `.claude/` - Claude Code workspace configuration

## Core Commands

### Running Agents

```bash
# Run an agent from template
cd agent-template/
python src/agent.py

# Run a specific agent instance
cd agents/remote-agent-sample/
python src/agent.py

# Run with custom environment
ENVIRONMENT=development python src/agent.py
```

### Testing

```bash
# Test multi-agent authentication forwarding
cd agent-template/
./testing_scripts/test_multiagent.sh

# Test specific agent
cd agents/remote-agent-sample/
python src/agent.py
```

### Development Setup

```bash
# Install dependencies for template
cd agent-template/
pip install -r requirements.txt

# Development dependencies (testing, type checking)
pip install -r requirements-dev.txt

# Run setup script for new agent
./deployment/scripts/setup.sh --dev
```

### Type Checking and Quality

```bash
# Type checking
mypy src/

# Testing
pytest

# Run with debug logging
LOG_LEVEL=DEBUG python src/agent.py
```

## Architecture Overview

### Template-Based Agent Creation
- All agents inherit from `agent-template/` with modular OAuth authentication
- Template provides complete A2A server implementation with authentication forwarding
- Agents support both standalone and multi-agent orchestration modes

### Authentication Flow
- OAuth 2.0 with multiple providers (Google, Azure, Okta)
- Bearer token forwarding for A2A communication
- Authentication context injection via `auth_context_callback`
- Secure credential storage via Google Secret Manager or environment variables

### Agent Communication
- A2A protocol for agent-to-agent communication (`agent_a2a/server.py`)
- Authentication context automatically forwarded to remote agents
- Remote agent factory pattern (`agent_factory/remote_agent_factory.py`)
- Dynamic sub-agent loading with auth context injection

### Configuration System
- `config/agent_config.yaml` - Agent settings and capabilities
- `config/oauth_config.yaml` - OAuth provider configuration
- `config/deployment_config.yaml` - Deployment settings
- Environment-specific configuration via `.env` files

## Key Files and Patterns

### Main Agent Implementation
- `src/agent.py` - Main entry point with OAuth + A2A server
- `src/auth/agent_auth_callback.py` - Authentication context injection
- `src/tools/authenticated_tool.py` - Base class for OAuth-aware tools

### Authentication System
- `src/auth/auth_config.py` - OAuth configuration loading
- `src/auth/oauth_middleware.py` - OAuth flow handling
- `src/auth/credential_store.py` - Secure token storage

### A2A Communication
- `src/agent_a2a/server.py` - A2A server with auth forwarding
- `src/agent_factory/remote_agent_factory.py` - Remote agent management

## Environment Configuration

Required environment variables:
```bash
GOOGLE_OAUTH_CLIENT_ID=your-client-id
GOOGLE_OAUTH_CLIENT_SECRET=your-client-secret
AGENT_NAME=YourAgentName
ENVIRONMENT=development|production
```

OAuth credentials should be configured in `.env` files (never committed) or Google Secret Manager for production.

## Creating New Agents

1. Copy template: `cp -r agent-template/ my-new-agent/`
2. Configure OAuth credentials in `.env`
3. Customize `config/agent_config.yaml` for specific capabilities
4. Implement custom tools inheriting from `AuthenticatedTool`
5. Test with `python src/agent.py`

## Multi-Agent Setup

- Configure remote agents in YAML files under `docs/configurations/`
- Use `docs/multi_agent_setup.md` for orchestration patterns
- Authentication context is automatically forwarded between agents
- Test multi-agent flows with `test_multiagent.sh`

## Security Considerations

- Never commit OAuth credentials to version control
- Use Google Secret Manager for production token storage
- All agent communication uses bearer token authentication
- Follow least-privilege IAM patterns for Google Cloud deployment