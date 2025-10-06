# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

This is an **Agent Factory** - a comprehensive toolkit for creating Google ADK (Agent Development Kit) agents with OAuth authentication, MCP (Model Context Protocol) integration, and Agent-to-Agent (A2A) protocol support. The repository uses a template-based approach for creating new agents with standardized authentication, tool registry, and communication patterns.

## Key Directory Structure

- `agent-template/` - Production-ready template for new ADK agents with OAuth + A2A + MCP
- `agents/` - Live agent instances created from the template
- `simplified-template/` - Lightweight template with basic authentication forwarding
- `example-mcp-server/` - Example MCP server for testing MCP toolkit integration
- `docs/` - Documentation and configuration templates
- `.claude/` - Claude Code workspace configuration

## Core Commands

### Running Agents

```bash
# Run main agent from template (port 8000)
cd agent-template/
python src/agent.py

# Run specific agent instance (port 8001)
cd agents/remote-agent-sample/
python src/agent.py

# Run with custom environment
ENVIRONMENT=development python src/agent.py

# Run with debug logging
LOG_LEVEL=DEBUG python src/agent.py
```

### Testing Multi-Agent Setup

```bash
# Start remote agent first (Terminal 1)
cd agents/remote-agent-sample/
python src/agent.py

# Start main agent (Terminal 2)
cd agent-template/
python src/agent.py

# Test authentication forwarding (Terminal 3)
cd agent-template/
./testing_scripts/test_multiagent.sh
```

### Testing MCP Integration

```bash
# Start MCP server (Terminal 1)
cd example-mcp-server/
python server.py

# Start agent with MCP toolkit (Terminal 2)
cd agent-template/
python src/agent.py
```

### Development Setup

```bash
# Install dependencies for template
cd agent-template/
pip install -r requirements.txt

# Type checking (no dedicated config file)
cd agent-template/
mypy src/

# Testing (pytest available but no dedicated test files in template)
pytest

# Install development dependencies (included in main requirements.txt)
pip install -r requirements.txt
```

## Architecture Overview

### Template-Based Agent Creation
- All agents inherit from `agent-template/` with OAuth authentication and tool registry
- Template provides complete A2A server implementation with authentication forwarding
- Agents support both standalone and multi-agent orchestration modes
- Modular tool system with MCP toolkit integration for external tools

### Tool Registry System
- Centralized tool management via `config/tool_registry.yaml`
- Environment-specific tool configurations (development/staging/production)
- Automatic tool discovery and loading from registry
- Native tools (built-in) and MCP toolkit tools (external) unified interface

### MCP Toolkit Integration
- Model Context Protocol support for external tools via HTTP
- JWT token-based authentication for MCP servers
- Automatic token refresh and caching
- Google Cloud credential integration for JWT generation

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
- `config/tool_registry.yaml` - Tool configuration and environment settings
- `config/mcp_toolsets.yaml` - MCP server and toolset configurations
- `config/remote_agents.yaml` - Remote agent endpoints and authentication
- `config/deployment_config.yaml` - Deployment settings
- Environment-specific configuration via `.env` files

## Key Files and Patterns

### Main Agent Implementation
- `src/agent.py` - Main entry point with OAuth + A2A server + tool registry
- `src/auth/agent_auth_callback.py` - Authentication context injection
- `src/tools/authenticated_tool.py` - Base class for OAuth-aware tools
- `src/tools/tool_registry.py` - Tool registry system and configuration loading
- `src/tools/mcp_toolkit.py` - MCP toolkit with JWT authentication

### Authentication System
- `src/auth/auth_config.py` - OAuth configuration loading
- `src/auth/oauth_middleware.py` - OAuth flow handling
- `src/auth/credential_store.py` - Secure token storage

### A2A Communication
- `src/agent_a2a/server.py` - A2A server with auth forwarding
- `src/agent_factory/remote_agent_factory.py` - Remote agent management

### Tool System
- `src/tools/example_tool.py` - Native tool examples (ExampleTool, BearerTokenPrintTool)
- `config/tool_registry.yaml` - Tool configuration and environment settings
- `config/mcp_toolsets.yaml` - MCP server configurations and JWT settings

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
4. Configure tools in `config/tool_registry.yaml` and `config/mcp_toolsets.yaml`
5. Implement custom tools inheriting from `AuthenticatedTool`
6. Test with `python src/agent.py`

## Multi-Agent Setup

- Configure remote agents in `config/remote_agents.yaml`
- Use `docs/configurations/` templates for different deployment scenarios
- Use `docs/multi_agent_setup.md` for orchestration patterns
- Authentication context is automatically forwarded between agents
- Test multi-agent flows with `./testing_scripts/test_multiagent.sh`

## Testing Complete Setup

For comprehensive testing including MCP integration:
1. Follow `agent-template/docs/complete_testing_guide.md`
2. Start MCP server: `cd example-mcp-server/ && python server.py`
3. Start remote agent: `cd agents/remote-agent-sample/ && python src/agent.py`
4. Start main agent: `cd agent-template/ && python src/agent.py`
5. Test authentication forwarding: `./testing_scripts/test_multiagent.sh`

## Security Considerations

- Never commit OAuth credentials to version control
- Use Google Secret Manager for production token storage
- All agent communication uses bearer token authentication
- Follow least-privilege IAM patterns for Google Cloud deployment