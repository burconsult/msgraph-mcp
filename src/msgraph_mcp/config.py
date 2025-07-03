"""
Configuration management for Microsoft Graph MCP Server.
"""

import os
from typing import Optional, List
from pydantic import BaseSettings, Field, validator
from enum import Enum


class AuthMethod(str, Enum):
    """Supported authentication methods for Microsoft Graph."""
    CLIENT_CREDENTIALS = "client_credentials"
    DEVICE_CODE = "device_code"
    INTERACTIVE = "interactive"
    MANAGED_IDENTITY = "managed_identity"
    AZURE_CLI = "azure_cli"


class GraphConfig(BaseSettings):
    """Configuration for Microsoft Graph MCP Server."""
    
    # Basic API Configuration
    graph_base_url: str = Field(
        default="https://graph.microsoft.com/beta",
        description="Microsoft Graph API base URL (beta endpoint)"
    )
    
    # Authentication Configuration
    auth_method: AuthMethod = Field(
        default=AuthMethod.CLIENT_CREDENTIALS,
        description="Authentication method to use"
    )
    
    # Azure AD App Registration Details
    tenant_id: Optional[str] = Field(
        default=None,
        description="Azure AD tenant ID"
    )
    
    client_id: Optional[str] = Field(
        default=None,
        description="Azure AD application (client) ID"
    )
    
    client_secret: Optional[str] = Field(
        default=None,
        description="Azure AD application client secret"
    )
    
    # Certificate Authentication (alternative to client secret)
    certificate_path: Optional[str] = Field(
        default=None,
        description="Path to certificate file for certificate-based auth"
    )
    
    certificate_thumbprint: Optional[str] = Field(
        default=None,
        description="Certificate thumbprint for certificate-based auth"
    )
    
    # Scopes and Permissions
    scopes: List[str] = Field(
        default=["https://graph.microsoft.com/.default"],
        description="OAuth scopes to request"
    )
    
    # Rate Limiting Configuration
    max_requests_per_second: int = Field(
        default=10,
        description="Maximum requests per second to Microsoft Graph"
    )
    
    max_concurrent_requests: int = Field(
        default=5,
        description="Maximum concurrent requests to Microsoft Graph"
    )
    
    # Timeout Configuration
    request_timeout: int = Field(
        default=30,
        description="Request timeout in seconds"
    )
    
    # Retry Configuration
    max_retries: int = Field(
        default=3,
        description="Maximum number of retries for failed requests"
    )
    
    retry_backoff_factor: float = Field(
        default=1.5,
        description="Backoff factor for retries"
    )
    
    # Logging Configuration
    log_level: str = Field(
        default="INFO",
        description="Logging level"
    )
    
    enable_debug_logging: bool = Field(
        default=False,
        description="Enable debug logging for Microsoft Graph requests"
    )
    
    # Security Configuration
    validate_ssl: bool = Field(
        default=True,
        description="Validate SSL certificates"
    )
    
    # MCP Server Configuration
    server_name: str = Field(
        default="msgraph-mcp",
        description="MCP server name"
    )
    
    server_version: str = Field(
        default="0.1.0",
        description="MCP server version"
    )
    
    # Resource Access Configuration
    enable_user_operations: bool = Field(
        default=True,
        description="Enable user-related operations"
    )
    
    enable_group_operations: bool = Field(
        default=True,
        description="Enable group-related operations"
    )
    
    enable_application_operations: bool = Field(
        default=True,
        description="Enable application-related operations"
    )
    
    enable_directory_operations: bool = Field(
        default=True,
        description="Enable directory-related operations"
    )
    
    enable_mail_operations: bool = Field(
        default=False,
        description="Enable mail-related operations (requires additional permissions)"
    )
    
    enable_calendar_operations: bool = Field(
        default=False,
        description="Enable calendar-related operations (requires additional permissions)"
    )
    
    enable_teams_operations: bool = Field(
        default=False,
        description="Enable Teams-related operations (requires additional permissions)"
    )
    
    # Pagination Configuration
    default_page_size: int = Field(
        default=25,
        ge=1,
        le=999,
        description="Default page size for paginated results"
    )
    
    max_page_size: int = Field(
        default=100,
        ge=1,
        le=999,
        description="Maximum page size for paginated results"
    )
    
    class Config:
        env_prefix = "MSGRAPH_"
        env_file = ".env"
        case_sensitive = False
    
    @validator("auth_method", pre=True)
    def validate_auth_method(cls, v):
        """Validate authentication method."""
        if isinstance(v, str):
            try:
                return AuthMethod(v.lower())
            except ValueError:
                raise ValueError(f"Invalid auth method: {v}")
        return v
    
    @validator("scopes")
    def validate_scopes(cls, v):
        """Validate scopes configuration."""
        if not v:
            return ["https://graph.microsoft.com/.default"]
        return v
    
    @validator("tenant_id")
    def validate_tenant_id(cls, v, values):
        """Validate tenant ID is provided for non-managed identity auth."""
        auth_method = values.get("auth_method")
        if auth_method != AuthMethod.MANAGED_IDENTITY and not v:
            raise ValueError("tenant_id is required for this authentication method")
        return v
    
    @validator("client_id")
    def validate_client_id(cls, v, values):
        """Validate client ID is provided for app-based auth."""
        auth_method = values.get("auth_method")
        if auth_method in [AuthMethod.CLIENT_CREDENTIALS, AuthMethod.DEVICE_CODE] and not v:
            raise ValueError("client_id is required for this authentication method")
        return v
    
    @validator("client_secret")
    def validate_client_secret(cls, v, values):
        """Validate client secret is provided for client credentials auth."""
        auth_method = values.get("auth_method")
        certificate_path = values.get("certificate_path")
        
        if auth_method == AuthMethod.CLIENT_CREDENTIALS and not v and not certificate_path:
            raise ValueError("client_secret or certificate_path is required for client_credentials auth")
        return v
    
    def get_auth_config(self) -> dict:
        """Get authentication configuration as a dictionary."""
        config = {
            "auth_method": self.auth_method,
            "tenant_id": self.tenant_id,
            "client_id": self.client_id,
            "scopes": self.scopes,
        }
        
        if self.client_secret:
            config["client_secret"] = self.client_secret
            
        if self.certificate_path:
            config["certificate_path"] = self.certificate_path
            config["certificate_thumbprint"] = self.certificate_thumbprint
            
        return config
    
    def get_request_config(self) -> dict:
        """Get request configuration as a dictionary."""
        return {
            "timeout": self.request_timeout,
            "max_retries": self.max_retries,
            "backoff_factor": self.retry_backoff_factor,
            "verify_ssl": self.validate_ssl,
        }
    
    def get_rate_limit_config(self) -> dict:
        """Get rate limiting configuration as a dictionary."""
        return {
            "max_requests_per_second": self.max_requests_per_second,
            "max_concurrent_requests": self.max_concurrent_requests,
        }


def load_config() -> GraphConfig:
    """Load configuration from environment variables and .env file."""
    return GraphConfig()