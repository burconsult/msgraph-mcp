"""
Microsoft Graph MCP Server

A Model Context Protocol (MCP) server implementation for Microsoft Graph v2 beta.
Provides standardized access to Microsoft 365 and Azure AD services through MCP.
"""

__version__ = "0.1.0"
__author__ = "MCP Microsoft Graph"
__description__ = "MCP server client implementation for Microsoft Graph v2 beta"

from .server import MCPGraphServer
from .auth import GraphAuthManager
from .config import GraphConfig

__all__ = ["MCPGraphServer", "GraphAuthManager", "GraphConfig"]