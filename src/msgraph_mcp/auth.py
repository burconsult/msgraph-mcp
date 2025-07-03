"""
Authentication management for Microsoft Graph MCP Server.
"""

import asyncio
import logging
from typing import Optional, Dict, Any
from datetime import datetime, timedelta

from azure.identity import (
    ClientSecretCredential,
    CertificateCredential,
    DeviceCodeCredential,
    InteractiveBrowserCredential,
    ManagedIdentityCredential,
    AzureCliCredential,
    ChainedTokenCredential
)
from azure.core.credentials import AccessToken
from azure.core.exceptions import ClientAuthenticationError

from .config import GraphConfig, AuthMethod

logger = logging.getLogger(__name__)


class GraphAuthManager:
    """Authentication manager for Microsoft Graph API."""
    
    def __init__(self, config: GraphConfig):
        """Initialize the authentication manager."""
        self.config = config
        self._credential: Optional[Any] = None
        self._token_cache: Dict[str, AccessToken] = {}
        self._setup_credential()
    
    def _setup_credential(self) -> None:
        """Set up the appropriate credential based on configuration."""
        try:
            if self.config.auth_method == AuthMethod.CLIENT_CREDENTIALS:
                self._setup_client_credentials()
            elif self.config.auth_method == AuthMethod.DEVICE_CODE:
                self._setup_device_code()
            elif self.config.auth_method == AuthMethod.INTERACTIVE:
                self._setup_interactive()
            elif self.config.auth_method == AuthMethod.MANAGED_IDENTITY:
                self._setup_managed_identity()
            elif self.config.auth_method == AuthMethod.AZURE_CLI:
                self._setup_azure_cli()
            else:
                raise ValueError(f"Unsupported auth method: {self.config.auth_method}")
            
            logger.info(f"Authentication configured using {self.config.auth_method}")
            
        except Exception as e:
            logger.error(f"Failed to setup authentication: {e}")
            raise
    
    def _setup_client_credentials(self) -> None:
        """Set up client credentials authentication."""
        if not self.config.tenant_id or not self.config.client_id:
            raise ValueError("tenant_id and client_id are required for client credentials auth")
        
        if self.config.client_secret:
            self._credential = ClientSecretCredential(
                tenant_id=self.config.tenant_id,
                client_id=self.config.client_id,
                client_secret=self.config.client_secret
            )
        elif self.config.certificate_path:
            self._credential = CertificateCredential(
                tenant_id=self.config.tenant_id,
                client_id=self.config.client_id,
                certificate_path=self.config.certificate_path
            )
        else:
            raise ValueError("Either client_secret or certificate_path is required")
    
    def _setup_device_code(self) -> None:
        """Set up device code authentication."""
        if not self.config.tenant_id or not self.config.client_id:
            raise ValueError("tenant_id and client_id are required for device code auth")
        
        self._credential = DeviceCodeCredential(
            tenant_id=self.config.tenant_id,
            client_id=self.config.client_id
        )
    
    def _setup_interactive(self) -> None:
        """Set up interactive browser authentication."""
        if not self.config.tenant_id or not self.config.client_id:
            raise ValueError("tenant_id and client_id are required for interactive auth")
        
        self._credential = InteractiveBrowserCredential(
            tenant_id=self.config.tenant_id,
            client_id=self.config.client_id
        )
    
    def _setup_managed_identity(self) -> None:
        """Set up managed identity authentication."""
        # Use system-assigned managed identity if no client_id is provided
        if self.config.client_id:
            self._credential = ManagedIdentityCredential(
                client_id=self.config.client_id
            )
        else:
            self._credential = ManagedIdentityCredential()
    
    def _setup_azure_cli(self) -> None:
        """Set up Azure CLI authentication."""
        self._credential = AzureCliCredential()
    
    async def get_access_token(self, scopes: Optional[list] = None) -> str:
        """
        Get an access token for Microsoft Graph.
        
        Args:
            scopes: List of scopes to request. If None, uses default scopes.
            
        Returns:
            Access token string.
            
        Raises:
            ClientAuthenticationError: If authentication fails.
        """
        if not self._credential:
            raise ClientAuthenticationError("No credential configured")
        
        if scopes is None:
            scopes = self.config.scopes
        
        scope_key = ",".join(sorted(scopes))
        
        # Check cache for valid token
        if scope_key in self._token_cache:
            cached_token = self._token_cache[scope_key]
            # Check if token is still valid (with 5 minute buffer)
            if cached_token.expires_on > datetime.now().timestamp() + 300:
                logger.debug("Using cached access token")
                return cached_token.token
        
        try:
            # Get new token
            logger.debug(f"Requesting new access token for scopes: {scopes}")
            token = await asyncio.get_event_loop().run_in_executor(
                None, 
                lambda: self._credential.get_token(*scopes)
            )
            
            # Cache the token
            self._token_cache[scope_key] = token
            logger.debug("Successfully obtained access token")
            
            return token.token
            
        except Exception as e:
            logger.error(f"Failed to get access token: {e}")
            raise ClientAuthenticationError(f"Authentication failed: {e}")
    
    async def verify_authentication(self) -> bool:
        """
        Verify that authentication is working by attempting to get a token.
        
        Returns:
            True if authentication is successful, False otherwise.
        """
        try:
            await self.get_access_token()
            return True
        except Exception as e:
            logger.error(f"Authentication verification failed: {e}")
            return False
    
    def clear_token_cache(self) -> None:
        """Clear the token cache."""
        self._token_cache.clear()
        logger.debug("Token cache cleared")
    
    def get_auth_headers(self, token: str) -> Dict[str, str]:
        """
        Get authentication headers for HTTP requests.
        
        Args:
            token: Access token string.
            
        Returns:
            Dictionary of headers.
        """
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
    
    async def get_auth_headers_async(self, scopes: Optional[list] = None) -> Dict[str, str]:
        """
        Get authentication headers for HTTP requests asynchronously.
        
        Args:
            scopes: List of scopes to request.
            
        Returns:
            Dictionary of headers.
        """
        token = await self.get_access_token(scopes)
        return self.get_auth_headers(token)
    
    def get_credential_info(self) -> Dict[str, Any]:
        """
        Get information about the configured credential.
        
        Returns:
            Dictionary with credential information.
        """
        info = {
            "auth_method": self.config.auth_method.value,
            "tenant_id": self.config.tenant_id,
            "client_id": self.config.client_id,
            "scopes": self.config.scopes,
            "credential_type": type(self._credential).__name__ if self._credential else None
        }
        
        return info


class AuthenticationError(Exception):
    """Custom exception for authentication errors."""
    pass


async def create_auth_manager(config: GraphConfig) -> GraphAuthManager:
    """
    Create and verify an authentication manager.
    
    Args:
        config: Graph configuration.
        
    Returns:
        Authenticated GraphAuthManager instance.
        
    Raises:
        AuthenticationError: If authentication setup or verification fails.
    """
    try:
        auth_manager = GraphAuthManager(config)
        
        # Verify authentication works
        if not await auth_manager.verify_authentication():
            raise AuthenticationError("Authentication verification failed")
        
        return auth_manager
        
    except Exception as e:
        logger.error(f"Failed to create authentication manager: {e}")
        raise AuthenticationError(f"Authentication setup failed: {e}")


def setup_fallback_credential(config: GraphConfig) -> ChainedTokenCredential:
    """
    Set up a fallback credential chain for maximum compatibility.
    
    Args:
        config: Graph configuration.
        
    Returns:
        ChainedTokenCredential with multiple fallback options.
    """
    credentials = []
    
    # Add managed identity if available
    try:
        if config.client_id:
            credentials.append(ManagedIdentityCredential(client_id=config.client_id))
        else:
            credentials.append(ManagedIdentityCredential())
    except Exception:
        pass
    
    # Add Azure CLI credential
    try:
        credentials.append(AzureCliCredential())
    except Exception:
        pass
    
    # Add client credentials if configured
    if config.tenant_id and config.client_id and config.client_secret:
        try:
            credentials.append(ClientSecretCredential(
                tenant_id=config.tenant_id,
                client_id=config.client_id,
                client_secret=config.client_secret
            ))
        except Exception:
            pass
    
    if not credentials:
        raise ValueError("No valid credentials could be configured")
    
    return ChainedTokenCredential(*credentials)