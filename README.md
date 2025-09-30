# Agent Factory

A comprehensive toolkit for creating Google ADK (Agent Development Kit) agents with OAuth authentication, A2A (Agent-to-Agent) protocol integration, and multi-agent orchestration capabilities.

## 📁 Repository Structure

```
agent-factory/
├── agent-template/          # Template for creating new agents
├── agents/                  # Live agent instances created from template
├── docs/                    # Documentation and configuration templates
└── .claude/                 # Claude Code workspace configuration
```

## 🗂️ Folder Descriptions

### `agent-template/`
**Purpose**: Production-ready template for building new ADK agents

**Contents**:
- **Complete agent implementation** with OAuth authentication and A2A protocol
- **Modular architecture** supporting standalone and multi-agent modes
- **Testing suite** for authentication forwarding and multi-agent scenarios
- **Deployment configurations** for various environments

**How to use**:
1. Copy the template: `cp -r agent-template/ my-new-agent/`
2. Follow the setup guide: `agent-template/docs/setup.md`
3. Customize tools and configuration for your specific use case

**Key files**:
- `src/agent.py` - Main agent implementation
- `src/tools/` - Agent tools and capabilities
- `docs/setup.md` - Complete setup instructions
- `config/` - Configuration files
- `testing_scripts/` - Test scripts for validation

### `agents/`
**Purpose**: Working agent instances built from the template

**Contents**:
- **Live agent deployments** for specific use cases
- **Sample implementations** demonstrating template capabilities
- **Testing agents** for validating authentication and A2A features

**Current agents**:
- `remote-agent-sample/` - Authentication validation and A2A testing agent
- `profile-agent/` - User profile management agent

**How to use**:
1. Browse existing agents for examples
2. Run agents directly for testing: `cd agents/[agent-name] && python src/agent.py`
3. Use as reference when building new agents

### `docs/`
**Purpose**: Documentation, guides, and configuration templates

**Contents**:
- **Setup guides** for different deployment scenarios
- **Configuration templates** (YAML files) for multi-agent setups
- **Troubleshooting documentation** for common issues
- **Architecture documentation** and best practices

**Key files**:
- `multi_agent_setup.md` - Guide for multi-agent orchestration
- `standalone_setup.md` - Guide for single agent deployment
- `troubleshooting.md` - Common issues and solutions
- `configurations/` - YAML templates for different environments

**How to use**:
1. Start with setup guides for your deployment scenario
2. Use configuration templates as starting points
3. Reference troubleshooting for common issues

### `.claude/`
**Purpose**: Claude Code workspace configuration

**Contents**: IDE settings and workspace configuration for Claude Code

## 🚀 Quick Start

### Creating a New Agent

1. **Copy the template**:
   ```bash
   cp -r agent-template/ my-new-agent/
   cd my-new-agent/
   ```

2. **Follow setup guide**:
   ```bash
   # Read the complete setup instructions
   cat docs/setup.md

   # Set up environment
   cp .env.example .env
   # Edit .env with your OAuth credentials
   ```

3. **Install and run**:
   ```bash
   pip install -r requirements.txt
   python src/agent.py
   ```

### Testing Authentication & A2A

1. **Use the testing agent**:
   ```bash
   cd agents/remote-agent-sample/
   python src/agent.py
   ```

2. **Run authentication tests**:
   ```bash
   # Test bearer token forwarding
   ./test_multiagent.sh
   ```

### Multi-Agent Setup

1. **Review configuration templates**:
   ```bash
   ls docs/configurations/
   # Choose appropriate template for your scenario
   ```

2. **Follow multi-agent guide**:
   ```bash
   cat docs/multi_agent_setup.md
   ```

## 🔧 Configuration

### Environment Setup
All agents require OAuth credentials configured in `.env` files:

```bash
# Google OAuth (required)
GOOGLE_OAUTH_CLIENT_ID=your-client-id
GOOGLE_OAUTH_CLIENT_SECRET=your-client-secret

# Azure OAuth (optional)
AZURE_OAUTH_CLIENT_ID=your-azure-client-id
AZURE_OAUTH_CLIENT_SECRET=your-azure-client-secret
```

### Multi-Agent Configuration
Use configuration templates in `docs/configurations/` for different scenarios:
- `minimal_remote_agents.yaml` - Basic setup
- `development_remote_agents.yaml` - Development environment
- `production_remote_agents.yaml` - Production deployment

## 📚 Documentation

- **Template Documentation**: `agent-template/README.md`
- **Setup Guide**: `docs/multi_agent_setup.md` or `docs/standalone_setup.md`
- **Troubleshooting**: `docs/troubleshooting.md`
- **Configuration Examples**: `docs/configurations/`

## 🧪 Testing

### Authentication Testing
```bash
# Test authentication forwarding
cd agents/remote-agent-sample/
./test_multiagent.sh
```

### Template Testing
```bash
# Run template test suite
cd agent-template/
./testing_scripts/run_tests.sh
```

## 🏗️ Architecture

This toolkit supports both **standalone agents** and **multi-agent orchestration**:

- **Standalone Mode**: Single agent with OAuth authentication
- **Multi-Agent Mode**: Root agent orchestrating multiple specialized remote agents
- **A2A Protocol**: Secure agent-to-agent communication with authentication forwarding
- **Template-Based**: Consistent agent structure and deployment patterns

## 📝 Contributing

1. Make changes to the `agent-template/` for new features
2. Test changes using agents in `agents/` directory
3. Update documentation in `docs/` as needed
4. Follow existing patterns for consistency

## 🔒 Security

- OAuth 2.0 authentication with multiple providers
- Bearer token forwarding for A2A communication
- Secure credential management
- Enterprise-grade security patterns

---

For detailed setup instructions, see the appropriate guide in `docs/` or `agent-template/docs/setup.md`.