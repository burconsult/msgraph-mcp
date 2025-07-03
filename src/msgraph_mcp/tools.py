"""
MCP Tools implementation for Microsoft Graph operations.
"""

import json
import logging
from typing import Any, Dict, List, Optional
from datetime import datetime

from mcp.types import Tool, TextContent
import mcp.types as types

from .config import GraphConfig
from .graph_client import GraphClient, GraphAPIError

logger = logging.getLogger(__name__)


class GraphToolsHandler:
    """Handler for Microsoft Graph MCP tools."""
    
    def __init__(self, config: GraphConfig, graph_client: GraphClient):
        """Initialize the tools handler."""
        self.config = config
        self.graph_client = graph_client
        self.tools = self._define_tools()
        
        logger.info(f"Graph tools handler initialized with {len(self.tools)} tools")
    
    def _define_tools(self) -> List[Tool]:
        """Define available tools based on configuration."""
        tools = []
        
        # Core tools (always available)
        tools.extend([
            Tool(
                name="get_me",
                description="Get the current authenticated user's profile information",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "select": {
                            "type": "string",
                            "description": "Comma-separated list of properties to include (e.g., 'displayName,mail,jobTitle')"
                        }
                    }
                }
            ),
            Tool(
                name="test_connection",
                description="Test the connection to Microsoft Graph API",
                inputSchema={
                    "type": "object",
                    "properties": {}
                }
            ),
            Tool(
                name="get_service_info",
                description="Get information about the Microsoft Graph service",
                inputSchema={
                    "type": "object",
                    "properties": {}
                }
            )
        ])
        
        # User operations
        if self.config.enable_user_operations:
            tools.extend([
                Tool(
                    name="list_users",
                    description="List users in the organization",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "filter": {
                                "type": "string",
                                "description": "OData filter expression (e.g., \"startswith(displayName,'John')\")"
                            },
                            "select": {
                                "type": "string",
                                "description": "Comma-separated list of properties to include"
                            },
                            "top": {
                                "type": "integer",
                                "description": "Maximum number of users to return (1-999)",
                                "minimum": 1,
                                "maximum": 999
                            },
                            "search": {
                                "type": "string",
                                "description": "Search query for users"
                            }
                        }
                    }
                ),
                Tool(
                    name="get_user",
                    description="Get detailed information about a specific user",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "user_id": {
                                "type": "string",
                                "description": "User ID, user principal name, or 'me' for current user"
                            },
                            "select": {
                                "type": "string",
                                "description": "Comma-separated list of properties to include"
                            }
                        },
                        "required": ["user_id"]
                    }
                ),
                Tool(
                    name="create_user",
                    description="Create a new user in the organization",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "display_name": {
                                "type": "string",
                                "description": "Display name for the user"
                            },
                            "user_principal_name": {
                                "type": "string",
                                "description": "User principal name (email-like identifier)"
                            },
                            "mail_nickname": {
                                "type": "string",
                                "description": "Mail nickname for the user"
                            },
                            "password": {
                                "type": "string",
                                "description": "Temporary password for the user"
                            },
                            "account_enabled": {
                                "type": "boolean",
                                "description": "Whether the account is enabled",
                                "default": True
                            },
                            "force_change_password": {
                                "type": "boolean",
                                "description": "Whether user must change password on first sign-in",
                                "default": True
                            }
                        },
                        "required": ["display_name", "user_principal_name", "mail_nickname", "password"]
                    }
                ),
                Tool(
                    name="update_user",
                    description="Update an existing user's properties",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "user_id": {
                                "type": "string",
                                "description": "User ID or user principal name"
                            },
                            "properties": {
                                "type": "object",
                                "description": "Properties to update (e.g., {'displayName': 'New Name', 'jobTitle': 'Manager'})"
                            }
                        },
                        "required": ["user_id", "properties"]
                    }
                ),
                Tool(
                    name="delete_user",
                    description="Delete a user from the organization",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "user_id": {
                                "type": "string",
                                "description": "User ID or user principal name"
                            }
                        },
                        "required": ["user_id"]
                    }
                )
            ])
        
        # Group operations
        if self.config.enable_group_operations:
            tools.extend([
                Tool(
                    name="list_groups",
                    description="List groups in the organization",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "filter": {
                                "type": "string",
                                "description": "OData filter expression"
                            },
                            "select": {
                                "type": "string",
                                "description": "Comma-separated list of properties to include"
                            },
                            "top": {
                                "type": "integer",
                                "description": "Maximum number of groups to return",
                                "minimum": 1,
                                "maximum": 999
                            }
                        }
                    }
                ),
                Tool(
                    name="get_group",
                    description="Get detailed information about a specific group",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "group_id": {
                                "type": "string",
                                "description": "Group ID"
                            },
                            "select": {
                                "type": "string",
                                "description": "Comma-separated list of properties to include"
                            }
                        },
                        "required": ["group_id"]
                    }
                ),
                Tool(
                    name="get_group_members",
                    description="Get members of a specific group",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "group_id": {
                                "type": "string",
                                "description": "Group ID"
                            },
                            "select": {
                                "type": "string",
                                "description": "Comma-separated list of properties to include"
                            },
                            "top": {
                                "type": "integer",
                                "description": "Maximum number of members to return",
                                "minimum": 1,
                                "maximum": 999
                            }
                        },
                        "required": ["group_id"]
                    }
                ),
                Tool(
                    name="add_group_member",
                    description="Add a user to a group",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "group_id": {
                                "type": "string",
                                "description": "Group ID"
                            },
                            "user_id": {
                                "type": "string",
                                "description": "User ID to add to the group"
                            }
                        },
                        "required": ["group_id", "user_id"]
                    }
                ),
                Tool(
                    name="remove_group_member",
                    description="Remove a user from a group",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "group_id": {
                                "type": "string",
                                "description": "Group ID"
                            },
                            "user_id": {
                                "type": "string",
                                "description": "User ID to remove from the group"
                            }
                        },
                        "required": ["group_id", "user_id"]
                    }
                )
            ])
        
        # Application operations
        if self.config.enable_application_operations:
            tools.extend([
                Tool(
                    name="list_applications",
                    description="List applications in the organization",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "filter": {
                                "type": "string",
                                "description": "OData filter expression"
                            },
                            "select": {
                                "type": "string",
                                "description": "Comma-separated list of properties to include"
                            },
                            "top": {
                                "type": "integer",
                                "description": "Maximum number of applications to return",
                                "minimum": 1,
                                "maximum": 999
                            }
                        }
                    }
                ),
                Tool(
                    name="get_application",
                    description="Get detailed information about a specific application",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "app_id": {
                                "type": "string",
                                "description": "Application ID"
                            },
                            "select": {
                                "type": "string",
                                "description": "Comma-separated list of properties to include"
                            }
                        },
                        "required": ["app_id"]
                    }
                ),
                Tool(
                    name="list_service_principals",
                    description="List service principals in the organization",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "filter": {
                                "type": "string",
                                "description": "OData filter expression"
                            },
                            "select": {
                                "type": "string",
                                "description": "Comma-separated list of properties to include"
                            },
                            "top": {
                                "type": "integer",
                                "description": "Maximum number of service principals to return",
                                "minimum": 1,
                                "maximum": 999
                            }
                        }
                    }
                )
            ])
        
        # Directory operations
        if self.config.enable_directory_operations:
            tools.extend([
                Tool(
                    name="get_organization",
                    description="Get organization information",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "select": {
                                "type": "string",
                                "description": "Comma-separated list of properties to include"
                            }
                        }
                    }
                ),
                Tool(
                    name="list_directory_roles",
                    description="List directory roles",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "select": {
                                "type": "string",
                                "description": "Comma-separated list of properties to include"
                            }
                        }
                    }
                ),
                Tool(
                    name="get_directory_role_members",
                    description="Get members of a directory role",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "role_id": {
                                "type": "string",
                                "description": "Directory role ID"
                            },
                            "select": {
                                "type": "string",
                                "description": "Comma-separated list of properties to include"
                            }
                        },
                        "required": ["role_id"]
                    }
                )
            ])
        
        return tools
    
    async def list_tools(self) -> List[Tool]:
        """List all available tools."""
        return self.tools
    
    async def call_tool(self, name: str, arguments: Dict[str, Any]) -> List[types.TextContent]:
        """Call a specific tool with the given arguments."""
        try:
            logger.debug(f"Calling tool: {name} with arguments: {arguments}")
            
            # Route to appropriate handler
            if name == "get_me":
                result = await self._get_me(arguments)
            elif name == "test_connection":
                result = await self._test_connection(arguments)
            elif name == "get_service_info":
                result = await self._get_service_info(arguments)
            elif name == "list_users":
                result = await self._list_users(arguments)
            elif name == "get_user":
                result = await self._get_user(arguments)
            elif name == "create_user":
                result = await self._create_user(arguments)
            elif name == "update_user":
                result = await self._update_user(arguments)
            elif name == "delete_user":
                result = await self._delete_user(arguments)
            elif name == "list_groups":
                result = await self._list_groups(arguments)
            elif name == "get_group":
                result = await self._get_group(arguments)
            elif name == "get_group_members":
                result = await self._get_group_members(arguments)
            elif name == "add_group_member":
                result = await self._add_group_member(arguments)
            elif name == "remove_group_member":
                result = await self._remove_group_member(arguments)
            elif name == "list_applications":
                result = await self._list_applications(arguments)
            elif name == "get_application":
                result = await self._get_application(arguments)
            elif name == "list_service_principals":
                result = await self._list_service_principals(arguments)
            elif name == "get_organization":
                result = await self._get_organization(arguments)
            elif name == "list_directory_roles":
                result = await self._list_directory_roles(arguments)
            elif name == "get_directory_role_members":
                result = await self._get_directory_role_members(arguments)
            else:
                raise ValueError(f"Unknown tool: {name}")
            
            # Format result as TextContent
            if isinstance(result, str):
                content = result
            else:
                content = json.dumps(result, indent=2, default=str)
            
            return [types.TextContent(type="text", text=content)]
            
        except Exception as e:
            logger.error(f"Error calling tool {name}: {e}")
            error_msg = f"Error executing tool '{name}': {str(e)}"
            return [types.TextContent(type="text", text=error_msg)]
    
    # Tool implementations
    async def _get_me(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Get current user information."""
        query_params = {}
        if "select" in args:
            query_params["$select"] = args["select"]
        
        return await self.graph_client.get("me", query_params)
    
    async def _test_connection(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Test the connection to Microsoft Graph."""
        is_connected = await self.graph_client.test_connection()
        return {
            "connected": is_connected,
            "timestamp": datetime.now().isoformat(),
            "service": "Microsoft Graph Beta"
        }
    
    async def _get_service_info(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Get service information."""
        return await self.graph_client.get_service_info()
    
    async def _list_users(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """List users."""
        query_params = {}
        
        if "filter" in args:
            query_params["$filter"] = args["filter"]
        if "select" in args:
            query_params["$select"] = args["select"]
        if "top" in args:
            query_params["$top"] = args["top"]
        if "search" in args:
            query_params["$search"] = args["search"]
            # Add ConsistencyLevel header for search
            # This will be handled by the graph client
        
        return await self.graph_client.get("users", query_params)
    
    async def _get_user(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Get user information."""
        user_id = args["user_id"]
        query_params = {}
        
        if "select" in args:
            query_params["$select"] = args["select"]
        
        return await self.graph_client.get(f"users/{user_id}", query_params)
    
    async def _create_user(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new user."""
        user_data = {
            "displayName": args["display_name"],
            "userPrincipalName": args["user_principal_name"],
            "mailNickname": args["mail_nickname"],
            "passwordProfile": {
                "password": args["password"],
                "forceChangePasswordNextSignIn": args.get("force_change_password", True)
            },
            "accountEnabled": args.get("account_enabled", True)
        }
        
        return await self.graph_client.post("users", user_data)
    
    async def _update_user(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Update a user."""
        user_id = args["user_id"]
        properties = args["properties"]
        
        await self.graph_client.patch(f"users/{user_id}", properties)
        return {"message": f"User {user_id} updated successfully"}
    
    async def _delete_user(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Delete a user."""
        user_id = args["user_id"]
        
        await self.graph_client.delete(f"users/{user_id}")
        return {"message": f"User {user_id} deleted successfully"}
    
    async def _list_groups(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """List groups."""
        query_params = {}
        
        if "filter" in args:
            query_params["$filter"] = args["filter"]
        if "select" in args:
            query_params["$select"] = args["select"]
        if "top" in args:
            query_params["$top"] = args["top"]
        
        return await self.graph_client.get("groups", query_params)
    
    async def _get_group(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Get group information."""
        group_id = args["group_id"]
        query_params = {}
        
        if "select" in args:
            query_params["$select"] = args["select"]
        
        return await self.graph_client.get(f"groups/{group_id}", query_params)
    
    async def _get_group_members(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Get group members."""
        group_id = args["group_id"]
        query_params = {}
        
        if "select" in args:
            query_params["$select"] = args["select"]
        if "top" in args:
            query_params["$top"] = args["top"]
        
        return await self.graph_client.get(f"groups/{group_id}/members", query_params)
    
    async def _add_group_member(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Add a member to a group."""
        group_id = args["group_id"]
        user_id = args["user_id"]
        
        member_data = {
            "@odata.id": f"https://graph.microsoft.com/beta/users/{user_id}"
        }
        
        await self.graph_client.post(f"groups/{group_id}/members/$ref", member_data)
        return {"message": f"User {user_id} added to group {group_id}"}
    
    async def _remove_group_member(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Remove a member from a group."""
        group_id = args["group_id"]
        user_id = args["user_id"]
        
        await self.graph_client.delete(f"groups/{group_id}/members/{user_id}/$ref")
        return {"message": f"User {user_id} removed from group {group_id}"}
    
    async def _list_applications(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """List applications."""
        query_params = {}
        
        if "filter" in args:
            query_params["$filter"] = args["filter"]
        if "select" in args:
            query_params["$select"] = args["select"]
        if "top" in args:
            query_params["$top"] = args["top"]
        
        return await self.graph_client.get("applications", query_params)
    
    async def _get_application(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Get application information."""
        app_id = args["app_id"]
        query_params = {}
        
        if "select" in args:
            query_params["$select"] = args["select"]
        
        return await self.graph_client.get(f"applications/{app_id}", query_params)
    
    async def _list_service_principals(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """List service principals."""
        query_params = {}
        
        if "filter" in args:
            query_params["$filter"] = args["filter"]
        if "select" in args:
            query_params["$select"] = args["select"]
        if "top" in args:
            query_params["$top"] = args["top"]
        
        return await self.graph_client.get("servicePrincipals", query_params)
    
    async def _get_organization(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Get organization information."""
        query_params = {}
        
        if "select" in args:
            query_params["$select"] = args["select"]
        
        return await self.graph_client.get("organization", query_params)
    
    async def _list_directory_roles(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """List directory roles."""
        query_params = {}
        
        if "select" in args:
            query_params["$select"] = args["select"]
        
        return await self.graph_client.get("directoryRoles", query_params)
    
    async def _get_directory_role_members(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Get directory role members."""
        role_id = args["role_id"]
        query_params = {}
        
        if "select" in args:
            query_params["$select"] = args["select"]
        
        return await self.graph_client.get(f"directoryRoles/{role_id}/members", query_params)