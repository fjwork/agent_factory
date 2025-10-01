 A2A Files: ADK Native vs Custom Code Analysis

  Overview of Library Dependencies

  🔧 ADK Native Libraries Used

  - google.adk.* - Core ADK framework components
  - a2a.* - A2A protocol implementation

  🏗️ Custom Code

  - Authentication integration layers
  - Configuration management
  - Custom routing and middleware

  File-by-File Analysis

  server.py - Hybrid: 60% ADK Native, 40% Custom

  ✅ ADK Native Functions:

  # Core ADK components (100% native)
  def _create_runner(self) -> Runner:
      return Runner(
          app_name=self.agent.name,
          agent=self.agent,
          artifact_service=InMemoryArtifactService(),    # ADK native
          session_service=InMemorySessionService(),      # ADK native
          memory_service=InMemoryMemoryService(),        # ADK native
      )

  def _create_executor(self) -> A2aAgentExecutor:
      return A2aAgentExecutor(                           # ADK native
          runner=self.runner,
          config=A2aAgentExecutorConfig()                # ADK native
      )

  # Legacy function (100% ADK native)
  def create_agent_a2a_server(agent: Agent, agent_card: AgentCard) -> A2AStarletteApplication:
      return A2AStarletteApplication(                    # ADK native
          agent_card=agent_card,
          http_handler=request_handler                   # Uses ADK DefaultRequestHandler
      )

  🔨 Custom Functions:

  # Authentication-enhanced server (100% custom)
  class AuthenticatedA2AServer:
      def __init__(self, agent, config_dir, environment):
          self.oauth_middleware = OAuthMiddleware()          # Custom auth
          self.card_builder = AgentCardBuilder()            # Custom card builder
          self.request_handler = AuthenticatedRequestHandler() # Custom auth handler

  # All HTTP route handlers (100% custom)
  async def _handle_a2a_request(self, request):           # Custom auth wrapper
  async def _handle_auth_initiate(self, request):         # Custom OAuth endpoints
  async def _handle_auth_complete(self, request):         # Custom OAuth endpoints
  async def _handle_dual_auth_status(self, request):      # Custom dual auth
  async def _handle_health(self, request):                # Custom health check

  # Starlette app setup (custom routing, ADK integration)
  def _create_app(self) -> Starlette:                     # Custom routing layer

  handlers.py - Hybrid: 30% ADK Native, 70% Custom

  ✅ ADK Native Functions:

  # Inheritance from ADK (base functionality)
  class AuthenticatedRequestHandler(DefaultRequestHandler):  # Extends ADK class
      def __init__(self, agent_executor: AgentExecutor, task_store: TaskStore):
          super().__init__(agent_executor, task_store)   # ADK native initialization

  # Core message processing (ADK native)
  async def handle_post(self, request):
      # ... custom auth logic ...
      result = await self.on_message_send(message_params, context)  # ADK native method

  # A2A types and context (ADK native)
  from a2a.types import MessageSendParams                # ADK native types
  from a2a.server.context import ServerCallContext       # ADK native context
  message_params = MessageSendParams.model_validate(params_data)  # ADK native validation

  🔨 Custom Functions:

  # All authentication logic (100% custom)
  async def handle_post(self, request) -> Response:
      user_context = await self.dual_auth_middleware.extract_auth_context(request)  # Custom
      await self._store_oauth_in_session_state(user_context, body)  # Custom
      await self._inject_auth_context_into_agent(user_context)     # Custom

  # Session state management (100% custom)
  async def _store_oauth_in_session_state(self, user_context, body):  # Custom
  async def _inject_auth_context_into_agent(self, user_context):       # Custom

  # Authentication endpoints (100% custom)
  async def handle_authenticated_extended_card(self, request):         # Custom
  async def handle_auth_status(self, request):                        # Custom
  def _extract_auth_info(self, state_dict):                          # Custom
  def get_auth_status(self):                                         # Custom

  agent_card.py - Hybrid: 40% ADK Native, 60% Custom

  ✅ ADK Native Functions:

  # A2A types and structures (100% native)
  from a2a.types import (
      AgentCard, AgentSkill, AgentCapabilities,          # ADK native types
      TransportProtocol, AgentProvider
  )

  # Agent card construction (ADK native structures)
  def create_agent_card(self, environment) -> AgentCard:
      capabilities = AgentCapabilities(streaming=True)    # ADK native
      skills = [AgentSkill(...) for skill in skills_config]  # ADK native

      return AgentCard(                                   # ADK native
          name=agent_name,
          version=version,
          capabilities=capabilities,
          skills=skills,
          # ... other ADK fields
      )

  🔨 Custom Functions:

  # Configuration management (100% custom)
  class AgentCardBuilder:                                 # Custom class
      def load_agent_config(self, environment):           # Custom config loading
      def _expand_env_vars(self, obj):                    # Custom env var expansion
      def _deep_merge(self, base, override):              # Custom config merging

  # Security schemes integration (custom + auth config)
  def _create_security_schemes(self):                     # Custom security integration
  def _create_transport_config(self):                     # Custom transport config

  # Custom configuration class
  @dataclass
  class AgentCardConfig:                                  # Custom config structure
      name: str
      version: str
      # ... custom fields

  Summary: ADK Native vs Custom Code

  📊 Functionality Breakdown

  | Component            | ADK Native | Custom Code | Purpose                                      |
  |----------------------|------------|-------------|----------------------------------------------|
  | Core A2A Protocol    | ✅ 100%     | -           | Message handling, JSON-RPC, agent execution  |
  | Agent Card Structure | ✅ 90%      | 🔨 10%      | A2A-compliant agent cards with custom config |
  | Session Management   | ✅ 80%      | 🔨 20%      | ADK sessions + custom auth state             |
  | Request Routing      | ✅ 30%      | 🔨 70%      | Basic routing + custom auth endpoints        |
  | Authentication       | -          | 🔨 100%     | OAuth, bearer tokens, dual auth              |
  | Configuration        | -          | 🔨 100%     | YAML loading, env vars, security schemes     |
  | Health Monitoring    | -          | 🔨 100%     | Custom health checks with auth status        |

  🏗️ Architecture Pattern

  ┌─────────────────────────────────────────────┐
  │              Custom Layer                   │
  │  • OAuth/Bearer Authentication             │
  │  • Configuration Management                │
  │  • Custom Routing & Middleware             │
  │  • Health Monitoring                       │
  └─────────────────┬───────────────────────────┘
                    │ Wraps & Extends
  ┌─────────────────▼───────────────────────────┐
  │               ADK Layer                     │
  │  • Agent Execution (Runner, Executor)      │
  │  • A2A Protocol (MessageSend, JSON-RPC)    │
  │  • Session Management (InMemorySession)    │
  │  • Agent Cards (AgentCard, AgentSkill)     │
  └─────────────────────────────────────────────┘

  🔍 Key Insights

  ADK Provides the Foundation:
  - ✅ Core A2A Protocol - JSON-RPC, message handling, agent execution
  - ✅ Agent Lifecycle - Runners, executors, session management
  - ✅ Type System - Agent cards, skills, capabilities, message formats
  - ✅ Transport Layer - HTTP server, request/response handling

  Custom Code Adds Enterprise Features:
  - 🔨 Authentication Layer - OAuth, bearer tokens, dual auth support
  - 🔨 Security Integration - Auth context forwarding, session state management
  - 🔨 Configuration System - YAML configs, environment overrides, secret management
  - 🔨 Operational Features - Health checks, monitoring, custom endpoints

  Design Philosophy:
  - Extend, Don't Replace - Custom classes inherit from ADK base classes
  - Composition Over Inheritance - Custom middleware wraps ADK components
  - Backward Compatibility - Legacy ADK-only functions still available
  - Enterprise Readiness - Authentication and operational features added as layers