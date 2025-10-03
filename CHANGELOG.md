# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.0] - 2025-01-10

### Added

#### 🛠️ Tool Registry System
- **New Tool Registry Architecture**: Complete centralized tool management system
  - `src/tools/tool_registry.py`: Core registry implementation with YAML configuration
  - `config/tool_registry.yaml`: Configuration file for traditional authenticated tools
  - Environment-specific tool enablement (development/staging/production)
  - Tool discovery, status monitoring, and lifecycle management
  - Support for both traditional AuthenticatedTool and MCP toolsets

#### 🌐 MCP Toolkit Integration
- **MCP Toolset Support**: Full Model Context Protocol integration
  - `src/tools/mcp_toolkit.py`: Enhanced MCPToolset with authentication
  - `config/mcp_toolsets.yaml`: Configuration file for MCP toolsets
  - Automatic JWT token management with expiration checking
  - Tool caching for performance optimization
  - Configurable authentication headers and retry logic
  - Google Cloud credentials integration

#### 🔐 Enhanced Authentication
- **Unified Authentication System**: Combined OAuth and JWT token management
  - Combined authentication callback for OAuth context + MCP auth injection
  - Automatic token refresh based on configurable thresholds (default: 15 minutes)
  - Bearer token forwarding to MCP servers
  - Authentication header injection (`X-Serverless-Authorization`, `Authorization`, etc.)

#### 📋 Configuration Management
- **YAML-Based Configuration**: Centralized tool and MCP configuration
  - Environment-specific overrides for different deployment environments
  - Template variables support (`${VAR_NAME:default_value}`)
  - Tool categorization and organization
  - Health check configuration for MCP services

#### 🚀 Performance Optimizations
- **Caching System**: Multi-level caching for improved performance
  - Tool discovery caching to prevent repeated API calls
  - JWT token caching with automatic refresh
  - Global cache management with monitoring and cleanup utilities

#### 📚 Documentation
- **Comprehensive Documentation**: New guides and updated existing docs
  - `docs/tool_registry_guide.md`: Complete tool registry and MCP toolkit guide
  - Updated main `README.md` with tool registry system information
  - Updated `agent-template/README.md` with new architecture details
  - Configuration examples and troubleshooting guides

### Changed

#### 🔄 Agent Template Updates
- **Enhanced Agent Creation**: `src/agent.py` completely refactored
  - Automatic tool loading from registry configuration
  - Combined authentication callback supporting both OAuth and MCP
  - Dynamic agent instruction generation based on available tools
  - Tool status logging and monitoring
  - Registry instance storage on agent for runtime access

#### 🏗️ Architecture Improvements
- **Modular Tool System**: Improved tool architecture
  - `src/tools/__init__.py`: Enhanced imports and convenience functions
  - Better separation of concerns between traditional and MCP tools
  - Unified tool interface for both tool types

#### 🔧 Configuration Schema
- **Expanded Configuration Support**: New configuration options
  - Environment-specific tool enablement and configuration
  - MCP server connection parameters and authentication settings
  - Retry logic, timeouts, and connection pooling configuration

### Technical Details

#### New Files Added
```
agent-template/
├── src/tools/
│   ├── tool_registry.py          # Tool registry system
│   ├── mcp_toolkit.py            # MCP toolkit integration
│   └── __init__.py               # Enhanced tool imports
├── config/
│   ├── tool_registry.yaml        # Tool configuration
│   └── mcp_toolsets.yaml         # MCP toolset configuration
├── docs/
│   └── tool_registry_guide.md    # Comprehensive usage guide
└── CHANGELOG.md                   # This changelog
```

#### Modified Files
```
agent-template/
├── src/
│   └── agent.py                   # Enhanced with tool registry integration
├── README.md                      # Updated with tool registry information
└── agent-template/README.md       # Enhanced documentation
```

#### Environment Variables
New environment variables supported:
- `MCP_SERVER_URL`: MCP server endpoint URL
- `TOKEN_REFRESH_THRESHOLD_MINS`: Token refresh threshold (default: 15)
- `ENABLE_WEATHER_MCP`: Enable weather MCP toolset (default: true)
- `LOG_LEVEL`: Enhanced logging support for debugging

#### Dependencies
- Enhanced support for existing Google ADK tools and MCP integration
- Improved JWT token handling with automatic refresh
- YAML configuration parsing and validation

### Security Enhancements
- **Token Security**: Automatic token lifecycle management
- **Header Security**: Configurable authentication headers
- **Environment Isolation**: Environment-specific security settings
- **Cache Security**: Secure token storage in caches

### Performance Improvements
- **Tool Loading**: Reduced startup time through intelligent caching
- **Memory Usage**: Optimized tool registry memory footprint
- **Network Efficiency**: Connection pooling and retry logic for MCP connections
- **Token Management**: Reduced authentication overhead through smart caching

### Backward Compatibility
- **Full Compatibility**: All existing functionality preserved
- **Migration Path**: Existing agents work without modification
- **Configuration**: New configuration files are optional - defaults provided
- **API Stability**: No breaking changes to existing tool interfaces

### Breaking Changes
- None - this release is fully backward compatible

### Migration Guide
For existing agents:
1. No immediate action required - new features are opt-in
2. To enable tool registry: copy new configuration files and update imports
3. To enable MCP toolkit: configure MCP server URLs and authentication
4. See `docs/tool_registry_guide.md` for detailed migration instructions

### Contributors
- Enhanced based on user-provided MCP toolkit sample code
- Integrated enterprise-grade patterns for production use
- Comprehensive testing and documentation

---

## [1.0.0] - Previous Release

### Added
- Initial OAuth authentication system
- A2A (Agent-to-Agent) protocol support
- Multi-agent orchestration capabilities
- Complete agent template structure
- Documentation and setup guides