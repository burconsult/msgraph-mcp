"""
Main MCP Server implementation for Microsoft Graph.
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional, Sequence
import json
from datetime import datetime

from mcp.server.models import InitializationOptions
from mcp.server import NotificationOptions, Server
from mcp.types import (
    Resource, Tool, Prompt, TextContent, ImageContent, EmbeddedResource,
    CallToolRequest, GetPromptRequest, GetResourceRequest, ListResourcesRequest,
    ListToolsRequest, ListPromptsRequest
)
import mcp.types as types

from .config import GraphConfig, load_config
from .auth import GraphAuthManager, create_auth_manager
from .graph_client import GraphClient, GraphAPIError
from .tools import GraphToolsHandler
from .resources import GraphResourcesHandler
from .prompts import GraphPromptsHandler

logger = logging.getLogger(__name__)


class MCPGraphServer:
    """Main MCP Server for Microsoft Graph integration."""
    
    def __init__(self, config: Optional[GraphConfig] = None):
        """Initialize the MCP Graph Server."""
        self.config = config or load_config()
        self.server = Server(self.config.server_name)
        self.auth_manager: Optional[GraphAuthManager] = None
        self.graph_client: Optional[GraphClient] = None
        self.tools_handler: Optional[GraphToolsHandler] = None
        self.resources_handler: Optional[GraphResourcesHandler] = None
        self.prompts_handler: Optional[GraphPromptsHandler] = None
        
        self._setup_handlers()
        
        logger.info(f"MCP Graph Server initialized: {self.config.server_name} v{self.config.server_version}")
    
    def _setup_handlers(self) -> None:
        """Set up MCP request handlers."""
        
        # Server initialization
        @self.server.list_resources()
        async def handle_list_resources() -> List[Resource]:
            """Handle list resources request."""
            if not self.resources_handler:
                return []
            return await self.resources_handler.list_resources()
        
        @self.server.get_resource()
        async def handle_get_resource(uri: str) -> str:
            """Handle get resource request."""
            if not self.resources_handler:
                raise ValueError("Resources handler not initialized")
            return await self.resources_handler.get_resource(uri)
        
        @self.server.list_tools()
        async def handle_list_tools() -> List[Tool]:
            """Handle list tools request."""
            if not self.tools_handler:
                return []
            return await self.tools_handler.list_tools()
        
        @self.server.call_tool()
        async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> List[types.TextContent | types.ImageContent | types.EmbeddedResource]:
            """Handle tool call request."""
            if not self.tools_handler:
                raise ValueError("Tools handler not initialized")
            return await self.tools_handler.call_tool(name, arguments)
        
        @self.server.list_prompts()
        async def handle_list_prompts() -> List[Prompt]:
            """Handle list prompts request."""
            if not self.prompts_handler:
                return []
            return await self.prompts_handler.list_prompts()
        
        @self.server.get_prompt()
        async def handle_get_prompt(name: str, arguments: Optional[Dict[str, str]] = None) -> types.GetPromptResult:
            """Handle get prompt request."""
            if not self.prompts_handler:
                raise ValueError("Prompts handler not initialized")
            return await self.prompts_handler.get_prompt(name, arguments or {})
    
    async def initialize(self) -> None:
        """Initialize the server components."""
        try:
            logger.info("Initializing MCP Graph Server...")
            
            # Initialize authentication
            self.auth_manager = await create_auth_manager(self.config)
            logger.info("Authentication manager initialized")
            
            # Initialize Graph client
            self.graph_client = GraphClient(self.config, self.auth_manager)
            logger.info("Graph client initialized")
            
            # Test connection
            if await self.graph_client.test_connection():
                logger.info("Microsoft Graph connection test successful")
            else:
                logger.warning("Microsoft Graph connection test failed")
            
            # Initialize handlers
            self.tools_handler = GraphToolsHandler(self.config, self.graph_client)
            self.resources_handler = GraphResourcesHandler(self.config, self.graph_client)
            self.prompts_handler = GraphPromptsHandler(self.config, self.graph_client)
            
            logger.info("All handlers initialized")
            logger.info("MCP Graph Server initialization complete")
            
        except Exception as e:
            logger.error(f"Failed to initialize server: {e}")
            raise
    
    async def cleanup(self) -> None:
        """Clean up server resources."""
        try:
            if self.graph_client:
                await self.graph_client.close()
            logger.info("Server cleanup complete")
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
    
    async def run(self) -> None:
        """Run the MCP server."""
        try:
            await self.initialize()
            
            # Setup notification options
            notification_options = NotificationOptions()
            
            # Setup initialization options
            init_options = InitializationOptions(
                server_name=self.config.server_name,
                server_version=self.config.server_version,
                capabilities=types.ServerCapabilities(
                    resources=types.ResourcesCapability(
                        subscribe=False,
                        list_changed=False
                    ),
                    tools=types.ToolsCapability(
                        list_changed=False
                    ),
                    prompts=types.PromptsCapability(
                        list_changed=False
                    ),
                    logging=types.LoggingCapability(),
                ),
            )
            
            # Run the server
            async with self.server:
                await self.server.run()
                
        except KeyboardInterrupt:
            logger.info("Server interrupted by user")
        except Exception as e:
            logger.error(f"Server error: {e}")
            raise
        finally:
            await self.cleanup()
    
    def get_server_info(self) -> Dict[str, Any]:
        """Get server information."""
        info = {
            "name": self.config.server_name,
            "version": self.config.server_version,
            "description": "MCP server for Microsoft Graph v2 beta",
            "graph_base_url": self.config.graph_base_url,
            "auth_method": self.config.auth_method.value if self.config.auth_method else None,
            "capabilities": {
                "users": self.config.enable_user_operations,
                "groups": self.config.enable_group_operations,
                "applications": self.config.enable_application_operations,
                "directory": self.config.enable_directory_operations,
                "mail": self.config.enable_mail_operations,
                "calendar": self.config.enable_calendar_operations,
                "teams": self.config.enable_teams_operations
            }
        }
        
        if self.auth_manager:
            info["auth_info"] = self.auth_manager.get_credential_info()
        
        return info


# Import handlers (these will be created in separate files)
from .tools import GraphToolsHandler
from .resources import GraphResourcesHandler
from .prompts import GraphPromptsHandler