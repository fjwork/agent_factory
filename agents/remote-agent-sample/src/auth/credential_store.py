"""
Credential Store Module

This module provides secure storage and retrieval of OAuth tokens and credentials
using various backends including memory, file system, and Google Cloud Secret Manager.
"""

import os
import json
import time
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Union
from dataclasses import dataclass, asdict
from cryptography.fernet import Fernet
import base64
import hashlib

try:
    from google.cloud import secretmanager
    GOOGLE_CLOUD_AVAILABLE = True
except ImportError:
    GOOGLE_CLOUD_AVAILABLE = False
    secretmanager = None

from .auth_config import TokenStorageType

logger = logging.getLogger(__name__)


@dataclass
class TokenData:
    """Token data structure."""
    access_token: str
    token_type: str = "Bearer"
    refresh_token: Optional[str] = None
    expires_at: Optional[float] = None
    scope: Optional[str] = None
    user_id: Optional[str] = None
    provider: Optional[str] = None
    extra_data: Dict[str, Any] = None

    def __post_init__(self):
        if self.extra_data is None:
            self.extra_data = {}

    def is_expired(self) -> bool:
        """Check if the token is expired."""
        if self.expires_at is None:
            return False
        return time.time() >= self.expires_at

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TokenData':
        """Create from dictionary."""
        return cls(**data)


class CredentialStore(ABC):
    """Abstract base class for credential storage."""

    @abstractmethod
    async def store_token(self, user_id: str, provider: str, token_data: TokenData) -> None:
        """Store token data for a user and provider."""
        pass

    @abstractmethod
    async def get_token(self, user_id: str, provider: str) -> Optional[TokenData]:
        """Retrieve token data for a user and provider."""
        pass

    @abstractmethod
    async def delete_token(self, user_id: str, provider: str) -> None:
        """Delete token data for a user and provider."""
        pass

    @abstractmethod
    async def list_user_tokens(self, user_id: str) -> Dict[str, TokenData]:
        """List all tokens for a user."""
        pass


class MemoryCredentialStore(CredentialStore):
    """In-memory credential store (for development/testing)."""

    def __init__(self, enable_encryption: bool = False):
        self._store: Dict[str, Dict[str, TokenData]] = {}
        self._encryption = enable_encryption
        self._fernet = None

        if self._encryption:
            key = Fernet.generate_key()
            self._fernet = Fernet(key)
            logger.warning("Using in-memory encryption with generated key. Tokens will be lost on restart.")

    def _get_key(self, user_id: str, provider: str) -> str:
        """Generate storage key."""
        return f"{user_id}:{provider}"

    async def store_token(self, user_id: str, provider: str, token_data: TokenData) -> None:
        """Store token data."""
        if user_id not in self._store:
            self._store[user_id] = {}

        token_data.user_id = user_id
        token_data.provider = provider

        self._store[user_id][provider] = token_data
        logger.debug(f"Stored token for user {user_id}, provider {provider}")

    async def get_token(self, user_id: str, provider: str) -> Optional[TokenData]:
        """Retrieve token data."""
        if user_id not in self._store or provider not in self._store[user_id]:
            return None

        token_data = self._store[user_id][provider]

        # Check if token is expired
        if token_data.is_expired():
            logger.info(f"Token expired for user {user_id}, provider {provider}")
            await self.delete_token(user_id, provider)
            return None

        return token_data

    async def delete_token(self, user_id: str, provider: str) -> None:
        """Delete token data."""
        if user_id in self._store and provider in self._store[user_id]:
            del self._store[user_id][provider]
            if not self._store[user_id]:  # Remove user if no providers left
                del self._store[user_id]
            logger.debug(f"Deleted token for user {user_id}, provider {provider}")

    async def list_user_tokens(self, user_id: str) -> Dict[str, TokenData]:
        """List all tokens for a user."""
        if user_id not in self._store:
            return {}

        # Filter out expired tokens
        valid_tokens = {}
        for provider, token_data in self._store[user_id].items():
            if not token_data.is_expired():
                valid_tokens[provider] = token_data
            else:
                # Clean up expired tokens
                await self.delete_token(user_id, provider)

        return valid_tokens


class FileCredentialStore(CredentialStore):
    """File-based credential store with encryption."""

    def __init__(self, storage_dir: str = ".credentials", enable_encryption: bool = True):
        self.storage_dir = storage_dir
        self._encryption = enable_encryption
        self._fernet = None

        # Create storage directory
        os.makedirs(storage_dir, mode=0o700, exist_ok=True)

        if self._encryption:
            self._init_encryption()

    def _init_encryption(self):
        """Initialize encryption."""
        key_file = os.path.join(self.storage_dir, ".key")

        if os.path.exists(key_file):
            # Load existing key
            with open(key_file, 'rb') as f:
                key = f.read()
        else:
            # Generate new key
            key = Fernet.generate_key()
            with open(key_file, 'wb') as f:
                f.write(key)
            os.chmod(key_file, 0o600)

        self._fernet = Fernet(key)

    def _get_file_path(self, user_id: str, provider: str) -> str:
        """Get file path for user/provider combination."""
        # Hash user_id for privacy
        user_hash = hashlib.sha256(user_id.encode()).hexdigest()[:16]
        filename = f"{user_hash}_{provider}.json"
        return os.path.join(self.storage_dir, filename)

    def _encrypt_data(self, data: str) -> str:
        """Encrypt data if encryption is enabled."""
        if self._encryption and self._fernet:
            encrypted = self._fernet.encrypt(data.encode())
            return base64.b64encode(encrypted).decode()
        return data

    def _decrypt_data(self, data: str) -> str:
        """Decrypt data if encryption is enabled."""
        if self._encryption and self._fernet:
            encrypted = base64.b64decode(data.encode())
            return self._fernet.decrypt(encrypted).decode()
        return data

    async def store_token(self, user_id: str, provider: str, token_data: TokenData) -> None:
        """Store token data."""
        token_data.user_id = user_id
        token_data.provider = provider

        file_path = self._get_file_path(user_id, provider)
        data = json.dumps(token_data.to_dict(), indent=2)

        if self._encryption:
            data = self._encrypt_data(data)

        with open(file_path, 'w') as f:
            f.write(data)

        os.chmod(file_path, 0o600)
        logger.debug(f"Stored token for user {user_id}, provider {provider}")

    async def get_token(self, user_id: str, provider: str) -> Optional[TokenData]:
        """Retrieve token data."""
        file_path = self._get_file_path(user_id, provider)

        if not os.path.exists(file_path):
            return None

        try:
            with open(file_path, 'r') as f:
                data = f.read()

            if self._encryption:
                data = self._decrypt_data(data)

            token_dict = json.loads(data)
            token_data = TokenData.from_dict(token_dict)

            # Check if token is expired
            if token_data.is_expired():
                logger.info(f"Token expired for user {user_id}, provider {provider}")
                await self.delete_token(user_id, provider)
                return None

            return token_data

        except Exception as e:
            logger.error(f"Failed to read token for user {user_id}, provider {provider}: {e}")
            return None

    async def delete_token(self, user_id: str, provider: str) -> None:
        """Delete token data."""
        file_path = self._get_file_path(user_id, provider)

        if os.path.exists(file_path):
            os.remove(file_path)
            logger.debug(f"Deleted token for user {user_id}, provider {provider}")

    async def list_user_tokens(self, user_id: str) -> Dict[str, TokenData]:
        """List all tokens for a user."""
        user_hash = hashlib.sha256(user_id.encode()).hexdigest()[:16]
        pattern = f"{user_hash}_"

        tokens = {}
        for filename in os.listdir(self.storage_dir):
            if filename.startswith(pattern) and filename.endswith('.json'):
                provider = filename[len(pattern):-5]  # Remove hash prefix and .json suffix
                token_data = await self.get_token(user_id, provider)
                if token_data:
                    tokens[provider] = token_data

        return tokens


class GoogleCloudCredentialStore(CredentialStore):
    """Google Cloud Secret Manager credential store."""

    def __init__(self, project_id: str, enable_encryption: bool = True):
        if not GOOGLE_CLOUD_AVAILABLE:
            raise ImportError("Google Cloud Secret Manager not available. Install google-cloud-secret-manager.")

        self.project_id = project_id
        self.client = secretmanager.SecretManagerServiceClient()
        self._encryption = enable_encryption
        self._fernet = None

        if self._encryption:
            self._init_encryption()

    def _init_encryption(self):
        """Initialize encryption using a master key from Secret Manager."""
        master_key_name = "adk-agent-master-key"
        secret_name = f"projects/{self.project_id}/secrets/{master_key_name}/versions/latest"

        try:
            response = self.client.access_secret_version(request={"name": secret_name})
            key = response.payload.data
        except Exception:
            # Create new master key
            key = Fernet.generate_key()
            self._create_secret(master_key_name, key)

        self._fernet = Fernet(key)

    def _create_secret(self, secret_id: str, secret_value: Union[str, bytes]) -> str:
        """Create a new secret in Secret Manager."""
        parent = f"projects/{self.project_id}"

        # Create the secret
        secret = self.client.create_secret(
            request={
                "parent": parent,
                "secret_id": secret_id,
                "secret": {"replication": {"automatic": {}}},
            }
        )

        # Add the secret version
        if isinstance(secret_value, str):
            secret_value = secret_value.encode()

        version = self.client.add_secret_version(
            request={"parent": secret.name, "payload": {"data": secret_value}}
        )

        logger.info(f"Created secret: {secret.name}")
        return version.name

    def _get_secret_name(self, user_id: str, provider: str) -> str:
        """Generate secret name for user/provider combination."""
        user_hash = hashlib.sha256(user_id.encode()).hexdigest()[:16]
        return f"adk-agent-token-{user_hash}-{provider}"

    def _encrypt_data(self, data: str) -> str:
        """Encrypt data if encryption is enabled."""
        if self._encryption and self._fernet:
            encrypted = self._fernet.encrypt(data.encode())
            return base64.b64encode(encrypted).decode()
        return data

    def _decrypt_data(self, data: str) -> str:
        """Decrypt data if encryption is enabled."""
        if self._encryption and self._fernet:
            encrypted = base64.b64decode(data.encode())
            return self._fernet.decrypt(encrypted).decode()
        return data

    async def store_token(self, user_id: str, provider: str, token_data: TokenData) -> None:
        """Store token data."""
        token_data.user_id = user_id
        token_data.provider = provider

        secret_id = self._get_secret_name(user_id, provider)
        data = json.dumps(token_data.to_dict())

        if self._encryption:
            data = self._encrypt_data(data)

        try:
            # Try to add a new version to existing secret
            secret_name = f"projects/{self.project_id}/secrets/{secret_id}"
            self.client.add_secret_version(
                request={"parent": secret_name, "payload": {"data": data.encode()}}
            )
        except Exception:
            # Create new secret if it doesn't exist
            self._create_secret(secret_id, data)

        logger.debug(f"Stored token for user {user_id}, provider {provider}")

    async def get_token(self, user_id: str, provider: str) -> Optional[TokenData]:
        """Retrieve token data."""
        secret_id = self._get_secret_name(user_id, provider)
        secret_name = f"projects/{self.project_id}/secrets/{secret_id}/versions/latest"

        try:
            response = self.client.access_secret_version(request={"name": secret_name})
            data = response.payload.data.decode()

            if self._encryption:
                data = self._decrypt_data(data)

            token_dict = json.loads(data)
            token_data = TokenData.from_dict(token_dict)

            # Check if token is expired
            if token_data.is_expired():
                logger.info(f"Token expired for user {user_id}, provider {provider}")
                await self.delete_token(user_id, provider)
                return None

            return token_data

        except Exception as e:
            logger.debug(f"Failed to retrieve token for user {user_id}, provider {provider}: {e}")
            return None

    async def delete_token(self, user_id: str, provider: str) -> None:
        """Delete token data."""
        secret_id = self._get_secret_name(user_id, provider)
        secret_name = f"projects/{self.project_id}/secrets/{secret_id}"

        try:
            self.client.delete_secret(request={"name": secret_name})
            logger.debug(f"Deleted token for user {user_id}, provider {provider}")
        except Exception as e:
            logger.debug(f"Failed to delete token for user {user_id}, provider {provider}: {e}")

    async def list_user_tokens(self, user_id: str) -> Dict[str, TokenData]:
        """List all tokens for a user."""
        user_hash = hashlib.sha256(user_id.encode()).hexdigest()[:16]
        prefix = f"adk-agent-token-{user_hash}-"

        parent = f"projects/{self.project_id}"
        tokens = {}

        try:
            for secret in self.client.list_secrets(request={"parent": parent}):
                secret_id = secret.name.split('/')[-1]
                if secret_id.startswith(prefix):
                    provider = secret_id[len(prefix):]
                    token_data = await self.get_token(user_id, provider)
                    if token_data:
                        tokens[provider] = token_data
        except Exception as e:
            logger.error(f"Failed to list tokens for user {user_id}: {e}")

        return tokens


def create_credential_store(
    storage_type: TokenStorageType,
    enable_encryption: bool = True,
    **kwargs
) -> CredentialStore:
    """Factory function to create credential store based on type."""

    if storage_type == TokenStorageType.MEMORY:
        return MemoryCredentialStore(enable_encryption=enable_encryption)

    elif storage_type == TokenStorageType.FILE:
        storage_dir = kwargs.get('storage_dir', '.credentials')
        return FileCredentialStore(storage_dir=storage_dir, enable_encryption=enable_encryption)

    elif storage_type == TokenStorageType.SECRET_MANAGER:
        project_id = kwargs.get('project_id') or os.getenv('GOOGLE_CLOUD_PROJECT')
        if not project_id:
            raise ValueError("project_id required for Secret Manager storage")
        return GoogleCloudCredentialStore(project_id=project_id, enable_encryption=enable_encryption)

    else:
        raise ValueError(f"Unsupported storage type: {storage_type}")