🗄️ Where Tokens Are Stored

  Token Storage Options (configured via TOKEN_STORAGE_TYPE):

  1. Memory Storage (MemoryCredentialStore)
  self._store: Dict[str, Dict[str, TokenData]] = {}
  # Structure: {user_id: {provider: TokenData}}
    - Location: In-memory dictionary
    - Persistence: Lost on restart
    - Good for: Development, testing
  2. File Storage (FileCredentialStore)
  # Location: .credentials/ directory
  # File name: {user_hash}_{provider}.json (encrypted)
    - Location: Encrypted files on disk
    - Persistence: Survives restarts
    - Good for: Single-instance production
  3. Secret Manager (GoogleCloudCredentialStore)
  # Location: Google Cloud Secret Manager
  # Secret name: adk-agent-token-{user_hash}-{provider}
    - Location: Google Cloud Secret Manager
    - Persistence: Cloud-managed
    - Good for: Production, distributed deployments

  ⏰ How Expiration Works

  Token Expiration Calculation (in oauth_middleware.py:321):
  expires_at = None
  if "expires_in" in token_data:
      expires_at = time.time() + token_data["expires_in"]
      # time.time() = current Unix timestamp
      # expires_in = seconds until expiration (from OAuth provider)

  Expiration Check (in credential_store.py:47-51):
  def is_expired(self) -> bool:
      """Check if the token is expired."""
      if self.expires_at is None:
          return False  # No expiration set = never expires
      return time.time() >= self.expires_at  # Current time >= expiration time

  🔄 Token Lifecycle Management

  When Getting Tokens (oauth_middleware.py:337-361):
  async def get_valid_token(self, user_id: str, provider_name: str) -> Optional[TokenData]:
      # 1. Get token from storage
      token_data = await self.credential_store.get_token(user_id, provider_name)

      # 2. If expired but has refresh_token, try to refresh
      if token_data.is_expired() and token_data.refresh_token:
          refreshed_token = await self._refresh_token(user_id, provider, token_data.refresh_token)
          return refreshed_token

      # 3. Return token only if not expired
      return token_data if not token_data.is_expired() else None

  Automatic Cleanup (in credential_store.py:122-127):
  async def get_token(self, user_id: str, provider: str) -> Optional[TokenData]:
      token_data = self._store[user_id][provider]

      # Check if token is expired
      if token_data.is_expired():
          logger.info(f"Token expired for user {user_id}, provider {provider}")
          await self.delete_token(user_id, provider)  # Auto-cleanup
          return None

      return token_data

  📋 Token Data Structure

  What's Stored (TokenData class):
  @dataclass
  class TokenData:
      access_token: str                    # The actual token
      token_type: str = "Bearer"           # Usually "Bearer"
      refresh_token: Optional[str] = None  # For automatic refresh
      expires_at: Optional[float] = None   # Unix timestamp when expires
      scope: Optional[str] = None          # OAuth scopes
      user_id: Optional[str] = None        # User identifier  
      provider: Optional[str] = None       # OAuth provider (google, azure)
      extra_data: Dict[str, Any] = None    # Additional OAuth response data

  🔍 Storage Key Format

  How Tokens Are Keyed:
  # Memory: {user_id: {provider: TokenData}}
  "user@example.com": {
      "google": TokenData(...),
      "azure": TokenData(...)
  }

  # File: {user_hash}_{provider}.json
  "a1b2c3d4e5f6_google.json"  # user_hash = SHA256(user_id)[:16]

  # Secret Manager: adk-agent-token-{user_hash}-{provider}
  "adk-agent-token-a1b2c3d4e5f6-google"

  ⚡ Expiration Scenarios

  Scenario 1: Valid Token
  # expires_at = 1640995200 (future timestamp)
  # time.time() = 1640991600 (current time)
  # is_expired() = False → Token returned

  Scenario 2: Expired Token with Refresh
  # expires_at = 1640991000 (past timestamp)  
  # time.time() = 1640991600 (current time)
  # is_expired() = True → Try refresh_token → New token returned

  Scenario 3: Expired Token without Refresh
  # expires_at = 1640991000 (past timestamp)
  # refresh_token = None
  # is_expired() = True → Token deleted → None returned → User must re-authenticate

  Summary

  - Storage: Memory/File/SecretManager based on config
  - Expiration: Unix timestamp comparison (time.time() >= expires_at)
  - Auto-refresh: Uses refresh_token when access_token expires
  - Auto-cleanup: Expired tokens automatically deleted
  - Fallback: If refresh fails, user must re-authenticate via OAuth device flow