#!/bin/bash

# Git commands to commit the ADK Agent Template with OAuth authentication

# Initialize git repository (if not already done)
git init

# Add remote repository
git remote add origin git@github.com:fjwork/agent_factory.git

# Add all files to staging
git add .

# Create comprehensive commit with detailed message
git commit -m "$(cat <<'EOF'
feat: Add comprehensive ADK Agent Template with OAuth IDP integration

## 🚀 Major Features Added

### OAuth Authentication System
- Multi-provider OAuth support (Google, Azure, Okta, custom IDPs)
- Multiple OAuth flows: Device Flow, Authorization Code, Client Credentials
- Secure token storage: Memory, file-based, and Google Cloud Secret Manager
- Automatic token refresh and lifecycle management
- JWT validation and user context management

### A2A Protocol Integration
- Full Agent-to-Agent protocol implementation with authentication
- Security schemes configuration (OAuth2, Bearer, API Key)
- Authenticated extended agent cards
- HTTP header-based credential transmission
- Request handlers with user context validation

### Deployment Infrastructure
- **Cloud Run**: Containerized serverless deployment with auto-scaling
- **Agent Engine**: Vertex AI managed deployment with native integration
- Multi-stage Docker configuration (development/production)
- Automated setup scripts with prerequisite validation
- Environment-specific configuration management

### Configuration System
- Environment-based YAML configuration (dev/staging/production)
- Template variable expansion with environment variable support
- Secure credential management with Secret Manager integration
- Configurable security policies and authentication requirements

## 📁 Project Structure

```
agent_factory/
├── src/
│   ├── auth/                     # OAuth authentication components
│   │   ├── auth_config.py        # Configuration management
│   │   ├── oauth_middleware.py   # OAuth flow implementation
│   │   └── credential_store.py   # Secure token storage
│   ├── a2a/                      # A2A protocol components
│   │   ├── agent_card.py         # Agent card generation
│   │   ├── server.py             # A2A server implementation
│   │   └── handlers.py           # Authenticated request handlers
│   ├── tools/                    # Agent tools with authentication
│   │   ├── authenticated_tool.py # Base authenticated tool class
│   │   └── examples/             # Example authenticated tools
│   └── agent.py                  # Main agent implementation
├── config/                       # Configuration files
│   ├── agent_config.yaml         # Agent settings and capabilities
│   ├── oauth_config.yaml         # OAuth provider configurations
│   └── deployment_config.yaml    # Deployment parameters
├── deployment/                   # Deployment automation
│   ├── cloud_run/               # Cloud Run deployment scripts
│   ├── agent_engine/            # Agent Engine deployment scripts
│   ├── docker/                  # Container configuration
│   └── scripts/                 # Setup and utility scripts
└── docs/                        # Comprehensive documentation
```

## 🔧 Technical Implementation

### Architecture Patterns
- **Modular Design**: Clear separation of auth, A2A, and tool components
- **Factory Pattern**: Tool creation and configuration management
- **Middleware Pattern**: OAuth authentication integration
- **Builder Pattern**: Agent card generation with security schemes

### Security Features
- **Token Encryption**: Cryptographic protection for stored credentials
- **User Isolation**: Per-user credential management and context
- **Audit Logging**: Comprehensive logging for security and compliance
- **HTTPS Enforcement**: Configurable security requirements
- **Principle of Least Privilege**: Minimal permission requirements

### Development Experience
- **Hot Reload**: Development mode with automatic code reloading
- **Environment Parity**: Consistent configuration across environments
- **Type Safety**: Full type hints and validation
- **Testing Support**: Built-in testing utilities and examples
- **Documentation**: Comprehensive setup and usage guides

## 🎯 Key Benefits

- **Enterprise Ready**: Production-grade authentication and authorization
- **Multi-Cloud**: Support for various deployment targets
- **Rapid Development**: Template-based quick start with best practices
- **Scalable**: Auto-scaling deployment configurations
- **Secure**: Industry-standard OAuth flows and credential management
- **Maintainable**: Clear architecture and comprehensive documentation

## 📚 Research Foundation

This implementation leverages extensive research using Context7 MCP server:
- Latest ADK framework patterns and best practices
- A2A protocol authentication mechanisms and security schemes
- OAuth integration patterns for AI agents
- Cloud deployment patterns for both Cloud Run and Agent Engine
- Enterprise-grade security and configuration management

## 🚀 Usage

1. **Quick Start**: `./deployment/scripts/setup.sh`
2. **OAuth Configuration**: Automated OAuth client setup
3. **Deploy to Cloud Run**: `python deployment/cloud_run/deploy.py`
4. **Deploy to Agent Engine**: `python deployment/agent_engine/deploy.py`

## 🔮 Future Enhancements

- Additional OAuth provider integrations
- Enhanced monitoring and observability
- Multi-tenant support
- Advanced security policies
- Integration with more Google Cloud services

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>
EOF
)"

# Push to main branch
git branch -M main
git push -u origin main

echo "✅ Comprehensive commit created and pushed!"
echo "🌐 Repository: https://github.com/fjwork/agent_factory"
echo "📋 Commit includes full ADK Agent Template with OAuth authentication"