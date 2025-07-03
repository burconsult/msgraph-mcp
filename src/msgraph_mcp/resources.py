"""
MCP Resources implementation for Microsoft Graph.
"""

import json
import logging
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse, parse_qs

from mcp.types import Resource
import mcp.types as types

from .config import GraphConfig
from .graph_client import GraphClient, GraphAPIError

logger = logging.getLogger(__name__)


class GraphResourcesHandler:
    """Handler for Microsoft Graph MCP resources."""
    
    def __init__(self, config: GraphConfig, graph_client: GraphClient):
        """Initialize the resources handler."""
        self.config = config
        self.graph_client = graph_client
        
        logger.info("Graph resources handler initialized")
    
    async def list_resources(self) -> List[Resource]:
        """List all available resources."""
        resources = []
        
        # Core resources (always available)
        resources.extend([
            Resource(
                uri="msgraph://me",
                name="Current User Profile",
                description="Profile information for the currently authenticated user",
                mimeType="application/json"
            ),
            Resource(
                uri="msgraph://organization",
                name="Organization Information",
                description="Information about the current organization/tenant",
                mimeType="application/json"
            ),
            Resource(
                uri="msgraph://service/info",
                name="Service Information",
                description="Information about the Microsoft Graph service",
                mimeType="application/json"
            )
        ])
        
        # User resources
        if self.config.enable_user_operations:
            resources.extend([
                Resource(
                    uri="msgraph://users",
                    name="Users Collection",
                    description="Collection of users in the organization",
                    mimeType="application/json"
                ),
                Resource(
                    uri="msgraph://users/schema",
                    name="User Schema",
                    description="Schema definition for user objects",
                    mimeType="application/json"
                ),
                Resource(
                    uri="msgraph://users/count",
                    name="Users Count",
                    description="Total count of users in the organization",
                    mimeType="application/json"
                )
            ])
        
        # Group resources
        if self.config.enable_group_operations:
            resources.extend([
                Resource(
                    uri="msgraph://groups",
                    name="Groups Collection",
                    description="Collection of groups in the organization",
                    mimeType="application/json"
                ),
                Resource(
                    uri="msgraph://groups/schema",
                    name="Group Schema",
                    description="Schema definition for group objects",
                    mimeType="application/json"
                ),
                Resource(
                    uri="msgraph://groups/count",
                    name="Groups Count",
                    description="Total count of groups in the organization",
                    mimeType="application/json"
                )
            ])
        
        # Application resources
        if self.config.enable_application_operations:
            resources.extend([
                Resource(
                    uri="msgraph://applications",
                    name="Applications Collection",
                    description="Collection of applications in the organization",
                    mimeType="application/json"
                ),
                Resource(
                    uri="msgraph://servicePrincipals",
                    name="Service Principals Collection",
                    description="Collection of service principals in the organization",
                    mimeType="application/json"
                ),
                Resource(
                    uri="msgraph://applications/schema",
                    name="Application Schema",
                    description="Schema definition for application objects",
                    mimeType="application/json"
                )
            ])
        
        # Directory resources
        if self.config.enable_directory_operations:
            resources.extend([
                Resource(
                    uri="msgraph://directoryRoles",
                    name="Directory Roles",
                    description="Collection of directory roles in the organization",
                    mimeType="application/json"
                ),
                Resource(
                    uri="msgraph://directory/schema",
                    name="Directory Schema",
                    description="Schema definitions for directory objects",
                    mimeType="application/json"
                )
            ])
        
        # Dynamic resources (these allow parameterized access)
        resources.extend([
            Resource(
                uri="msgraph://users/{id}",
                name="Specific User",
                description="Get information about a specific user by ID or UPN",
                mimeType="application/json"
            ),
            Resource(
                uri="msgraph://groups/{id}",
                name="Specific Group",
                description="Get information about a specific group by ID",
                mimeType="application/json"
            ),
            Resource(
                uri="msgraph://groups/{id}/members",
                name="Group Members",
                description="Get members of a specific group",
                mimeType="application/json"
            ),
            Resource(
                uri="msgraph://applications/{id}",
                name="Specific Application",
                description="Get information about a specific application by ID",
                mimeType="application/json"
            ),
            Resource(
                uri="msgraph://servicePrincipals/{id}",
                name="Specific Service Principal",
                description="Get information about a specific service principal by ID",
                mimeType="application/json"
            ),
            Resource(
                uri="msgraph://directoryRoles/{id}/members",
                name="Directory Role Members",
                description="Get members of a specific directory role",
                mimeType="application/json"
            )
        ])
        
        logger.debug(f"Listed {len(resources)} available resources")
        return resources
    
    async def get_resource(self, uri: str) -> str:
        """Get the content of a specific resource."""
        try:
            logger.debug(f"Getting resource: {uri}")
            
            # Parse the URI
            parsed_uri = urlparse(uri)
            if parsed_uri.scheme != "msgraph":
                raise ValueError(f"Invalid scheme: {parsed_uri.scheme}")
            
            path = parsed_uri.path.lstrip('/')
            query_params = parse_qs(parsed_uri.query)
            
            # Extract select parameters if provided
            select_param = query_params.get('select', [None])[0]
            top_param = query_params.get('top', [None])[0]
            filter_param = query_params.get('filter', [None])[0]
            
            # Route to appropriate handler
            if path == "me":
                result = await self._get_me_resource(select_param)
            elif path == "organization":
                result = await self._get_organization_resource(select_param)
            elif path == "service/info":
                result = await self._get_service_info_resource()
            elif path == "users":
                result = await self._get_users_resource(select_param, top_param, filter_param)
            elif path == "users/schema":
                result = await self._get_user_schema_resource()
            elif path == "users/count":
                result = await self._get_users_count_resource()
            elif path == "groups":
                result = await self._get_groups_resource(select_param, top_param, filter_param)
            elif path == "groups/schema":
                result = await self._get_group_schema_resource()
            elif path == "groups/count":
                result = await self._get_groups_count_resource()
            elif path == "applications":
                result = await self._get_applications_resource(select_param, top_param, filter_param)
            elif path == "applications/schema":
                result = await self._get_application_schema_resource()
            elif path == "servicePrincipals":
                result = await self._get_service_principals_resource(select_param, top_param, filter_param)
            elif path == "directoryRoles":
                result = await self._get_directory_roles_resource(select_param)
            elif path == "directory/schema":
                result = await self._get_directory_schema_resource()
            elif path.startswith("users/"):
                result = await self._get_specific_user_resource(path, select_param)
            elif path.startswith("groups/"):
                result = await self._get_specific_group_resource(path, select_param)
            elif path.startswith("applications/"):
                result = await self._get_specific_application_resource(path, select_param)
            elif path.startswith("servicePrincipals/"):
                result = await self._get_specific_service_principal_resource(path, select_param)
            elif path.startswith("directoryRoles/"):
                result = await self._get_specific_directory_role_resource(path, select_param)
            else:
                raise ValueError(f"Unknown resource path: {path}")
            
            # Return JSON string
            return json.dumps(result, indent=2, default=str)
            
        except Exception as e:
            logger.error(f"Error getting resource {uri}: {e}")
            error_result = {
                "error": {
                    "message": str(e),
                    "resource": uri,
                    "timestamp": str(None)
                }
            }
            return json.dumps(error_result, indent=2)
    
    # Resource implementations
    async def _get_me_resource(self, select_param: Optional[str]) -> Dict[str, Any]:
        """Get current user resource."""
        query_params = {}
        if select_param:
            query_params["$select"] = select_param
        
        user_data = await self.graph_client.get("me", query_params)
        
        return {
            "type": "user",
            "source": "msgraph://me",
            "data": user_data,
            "metadata": {
                "description": "Current authenticated user profile",
                "lastUpdated": str(None)
            }
        }
    
    async def _get_organization_resource(self, select_param: Optional[str]) -> Dict[str, Any]:
        """Get organization resource."""
        query_params = {}
        if select_param:
            query_params["$select"] = select_param
        
        org_data = await self.graph_client.get("organization", query_params)
        
        return {
            "type": "organization",
            "source": "msgraph://organization",
            "data": org_data,
            "metadata": {
                "description": "Organization/tenant information",
                "lastUpdated": str(None)
            }
        }
    
    async def _get_service_info_resource(self) -> Dict[str, Any]:
        """Get service information resource."""
        service_info = await self.graph_client.get_service_info()
        
        return {
            "type": "service",
            "source": "msgraph://service/info",
            "data": service_info,
            "metadata": {
                "description": "Microsoft Graph service information",
                "lastUpdated": str(None)
            }
        }
    
    async def _get_users_resource(self, select_param: Optional[str], top_param: Optional[str], filter_param: Optional[str]) -> Dict[str, Any]:
        """Get users collection resource."""
        query_params = {}
        if select_param:
            query_params["$select"] = select_param
        if top_param:
            query_params["$top"] = min(int(top_param), self.config.max_page_size)
        else:
            query_params["$top"] = self.config.default_page_size
        if filter_param:
            query_params["$filter"] = filter_param
        
        users_data = await self.graph_client.get("users", query_params)
        
        return {
            "type": "collection",
            "source": "msgraph://users",
            "data": users_data,
            "metadata": {
                "description": "Users in the organization",
                "itemType": "user",
                "count": len(users_data.get("value", [])),
                "hasMore": "@odata.nextLink" in users_data,
                "lastUpdated": str(None)
            }
        }
    
    async def _get_user_schema_resource(self) -> Dict[str, Any]:
        """Get user schema resource."""
        schema = {
            "type": "object",
            "properties": {
                "id": {"type": "string", "description": "Unique identifier"},
                "displayName": {"type": "string", "description": "Display name"},
                "userPrincipalName": {"type": "string", "description": "User principal name"},
                "mail": {"type": "string", "description": "Email address"},
                "mailNickname": {"type": "string", "description": "Mail nickname"},
                "givenName": {"type": "string", "description": "First name"},
                "surname": {"type": "string", "description": "Last name"},
                "jobTitle": {"type": "string", "description": "Job title"},
                "department": {"type": "string", "description": "Department"},
                "officeLocation": {"type": "string", "description": "Office location"},
                "businessPhones": {"type": "array", "description": "Business phone numbers"},
                "mobilePhone": {"type": "string", "description": "Mobile phone number"},
                "accountEnabled": {"type": "boolean", "description": "Account enabled status"},
                "createdDateTime": {"type": "string", "description": "Creation date and time"},
                "lastSignInDateTime": {"type": "string", "description": "Last sign-in date and time"}
            }
        }
        
        return {
            "type": "schema",
            "source": "msgraph://users/schema",
            "data": schema,
            "metadata": {
                "description": "Schema definition for user objects",
                "objectType": "user",
                "lastUpdated": str(None)
            }
        }
    
    async def _get_users_count_resource(self) -> Dict[str, Any]:
        """Get users count resource."""
        try:
            # Get count using $count parameter
            count_data = await self.graph_client.get("users/$count")
            count = count_data if isinstance(count_data, int) else 0
        except Exception:
            # Fallback to getting first page and counting
            users_data = await self.graph_client.get("users", {"$top": "1"})
            count = len(users_data.get("value", []))
        
        return {
            "type": "count",
            "source": "msgraph://users/count",
            "data": {"count": count},
            "metadata": {
                "description": "Total count of users",
                "lastUpdated": str(None)
            }
        }
    
    async def _get_groups_resource(self, select_param: Optional[str], top_param: Optional[str], filter_param: Optional[str]) -> Dict[str, Any]:
        """Get groups collection resource."""
        query_params = {}
        if select_param:
            query_params["$select"] = select_param
        if top_param:
            query_params["$top"] = min(int(top_param), self.config.max_page_size)
        else:
            query_params["$top"] = self.config.default_page_size
        if filter_param:
            query_params["$filter"] = filter_param
        
        groups_data = await self.graph_client.get("groups", query_params)
        
        return {
            "type": "collection",
            "source": "msgraph://groups",
            "data": groups_data,
            "metadata": {
                "description": "Groups in the organization",
                "itemType": "group",
                "count": len(groups_data.get("value", [])),
                "hasMore": "@odata.nextLink" in groups_data,
                "lastUpdated": str(None)
            }
        }
    
    async def _get_group_schema_resource(self) -> Dict[str, Any]:
        """Get group schema resource."""
        schema = {
            "type": "object",
            "properties": {
                "id": {"type": "string", "description": "Unique identifier"},
                "displayName": {"type": "string", "description": "Display name"},
                "description": {"type": "string", "description": "Group description"},
                "mail": {"type": "string", "description": "Email address"},
                "mailNickname": {"type": "string", "description": "Mail nickname"},
                "mailEnabled": {"type": "boolean", "description": "Mail enabled status"},
                "securityEnabled": {"type": "boolean", "description": "Security enabled status"},
                "groupTypes": {"type": "array", "description": "Group types"},
                "visibility": {"type": "string", "description": "Group visibility"},
                "createdDateTime": {"type": "string", "description": "Creation date and time"},
                "renewedDateTime": {"type": "string", "description": "Last renewed date and time"}
            }
        }
        
        return {
            "type": "schema",
            "source": "msgraph://groups/schema",
            "data": schema,
            "metadata": {
                "description": "Schema definition for group objects",
                "objectType": "group",
                "lastUpdated": str(None)
            }
        }
    
    async def _get_groups_count_resource(self) -> Dict[str, Any]:
        """Get groups count resource."""
        try:
            count_data = await self.graph_client.get("groups/$count")
            count = count_data if isinstance(count_data, int) else 0
        except Exception:
            groups_data = await self.graph_client.get("groups", {"$top": "1"})
            count = len(groups_data.get("value", []))
        
        return {
            "type": "count",
            "source": "msgraph://groups/count",
            "data": {"count": count},
            "metadata": {
                "description": "Total count of groups",
                "lastUpdated": str(None)
            }
        }
    
    async def _get_applications_resource(self, select_param: Optional[str], top_param: Optional[str], filter_param: Optional[str]) -> Dict[str, Any]:
        """Get applications collection resource."""
        query_params = {}
        if select_param:
            query_params["$select"] = select_param
        if top_param:
            query_params["$top"] = min(int(top_param), self.config.max_page_size)
        else:
            query_params["$top"] = self.config.default_page_size
        if filter_param:
            query_params["$filter"] = filter_param
        
        apps_data = await self.graph_client.get("applications", query_params)
        
        return {
            "type": "collection",
            "source": "msgraph://applications",
            "data": apps_data,
            "metadata": {
                "description": "Applications in the organization",
                "itemType": "application",
                "count": len(apps_data.get("value", [])),
                "hasMore": "@odata.nextLink" in apps_data,
                "lastUpdated": str(None)
            }
        }
    
    async def _get_application_schema_resource(self) -> Dict[str, Any]:
        """Get application schema resource."""
        schema = {
            "type": "object",
            "properties": {
                "id": {"type": "string", "description": "Unique identifier"},
                "appId": {"type": "string", "description": "Application ID"},
                "displayName": {"type": "string", "description": "Display name"},
                "description": {"type": "string", "description": "Application description"},
                "publisherDomain": {"type": "string", "description": "Publisher domain"},
                "signInAudience": {"type": "string", "description": "Sign-in audience"},
                "tags": {"type": "array", "description": "Application tags"},
                "createdDateTime": {"type": "string", "description": "Creation date and time"}
            }
        }
        
        return {
            "type": "schema",
            "source": "msgraph://applications/schema",
            "data": schema,
            "metadata": {
                "description": "Schema definition for application objects",
                "objectType": "application",
                "lastUpdated": str(None)
            }
        }
    
    async def _get_service_principals_resource(self, select_param: Optional[str], top_param: Optional[str], filter_param: Optional[str]) -> Dict[str, Any]:
        """Get service principals collection resource."""
        query_params = {}
        if select_param:
            query_params["$select"] = select_param
        if top_param:
            query_params["$top"] = min(int(top_param), self.config.max_page_size)
        else:
            query_params["$top"] = self.config.default_page_size
        if filter_param:
            query_params["$filter"] = filter_param
        
        sp_data = await self.graph_client.get("servicePrincipals", query_params)
        
        return {
            "type": "collection",
            "source": "msgraph://servicePrincipals",
            "data": sp_data,
            "metadata": {
                "description": "Service principals in the organization",
                "itemType": "servicePrincipal",
                "count": len(sp_data.get("value", [])),
                "hasMore": "@odata.nextLink" in sp_data,
                "lastUpdated": str(None)
            }
        }
    
    async def _get_directory_roles_resource(self, select_param: Optional[str]) -> Dict[str, Any]:
        """Get directory roles resource."""
        query_params = {}
        if select_param:
            query_params["$select"] = select_param
        
        roles_data = await self.graph_client.get("directoryRoles", query_params)
        
        return {
            "type": "collection",
            "source": "msgraph://directoryRoles",
            "data": roles_data,
            "metadata": {
                "description": "Directory roles in the organization",
                "itemType": "directoryRole",
                "count": len(roles_data.get("value", [])),
                "lastUpdated": str(None)
            }
        }
    
    async def _get_directory_schema_resource(self) -> Dict[str, Any]:
        """Get directory schema resource."""
        schema = {
            "users": {
                "endpoint": "/users",
                "description": "User objects in the directory"
            },
            "groups": {
                "endpoint": "/groups",
                "description": "Group objects in the directory"
            },
            "applications": {
                "endpoint": "/applications",
                "description": "Application objects in the directory"
            },
            "servicePrincipals": {
                "endpoint": "/servicePrincipals",
                "description": "Service principal objects in the directory"
            },
            "directoryRoles": {
                "endpoint": "/directoryRoles",
                "description": "Directory role objects"
            },
            "organization": {
                "endpoint": "/organization",
                "description": "Organization information"
            }
        }
        
        return {
            "type": "schema",
            "source": "msgraph://directory/schema",
            "data": schema,
            "metadata": {
                "description": "Schema definitions for directory objects",
                "lastUpdated": str(None)
            }
        }
    
    # Dynamic resource handlers
    async def _get_specific_user_resource(self, path: str, select_param: Optional[str]) -> Dict[str, Any]:
        """Get specific user resource."""
        user_id = path.split("/")[1]
        query_params = {}
        if select_param:
            query_params["$select"] = select_param
        
        user_data = await self.graph_client.get(f"users/{user_id}", query_params)
        
        return {
            "type": "user",
            "source": f"msgraph://users/{user_id}",
            "data": user_data,
            "metadata": {
                "description": f"User information for {user_id}",
                "lastUpdated": str(None)
            }
        }
    
    async def _get_specific_group_resource(self, path: str, select_param: Optional[str]) -> Dict[str, Any]:
        """Get specific group resource."""
        parts = path.split("/")
        group_id = parts[1]
        
        if len(parts) > 2 and parts[2] == "members":
            # Get group members
            query_params = {}
            if select_param:
                query_params["$select"] = select_param
            
            members_data = await self.graph_client.get(f"groups/{group_id}/members", query_params)
            
            return {
                "type": "collection",
                "source": f"msgraph://groups/{group_id}/members",
                "data": members_data,
                "metadata": {
                    "description": f"Members of group {group_id}",
                    "itemType": "user",
                    "count": len(members_data.get("value", [])),
                    "hasMore": "@odata.nextLink" in members_data,
                    "lastUpdated": str(None)
                }
            }
        else:
            # Get group info
            query_params = {}
            if select_param:
                query_params["$select"] = select_param
            
            group_data = await self.graph_client.get(f"groups/{group_id}", query_params)
            
            return {
                "type": "group",
                "source": f"msgraph://groups/{group_id}",
                "data": group_data,
                "metadata": {
                    "description": f"Group information for {group_id}",
                    "lastUpdated": str(None)
                }
            }
    
    async def _get_specific_application_resource(self, path: str, select_param: Optional[str]) -> Dict[str, Any]:
        """Get specific application resource."""
        app_id = path.split("/")[1]
        query_params = {}
        if select_param:
            query_params["$select"] = select_param
        
        app_data = await self.graph_client.get(f"applications/{app_id}", query_params)
        
        return {
            "type": "application",
            "source": f"msgraph://applications/{app_id}",
            "data": app_data,
            "metadata": {
                "description": f"Application information for {app_id}",
                "lastUpdated": str(None)
            }
        }
    
    async def _get_specific_service_principal_resource(self, path: str, select_param: Optional[str]) -> Dict[str, Any]:
        """Get specific service principal resource."""
        sp_id = path.split("/")[1]
        query_params = {}
        if select_param:
            query_params["$select"] = select_param
        
        sp_data = await self.graph_client.get(f"servicePrincipals/{sp_id}", query_params)
        
        return {
            "type": "servicePrincipal",
            "source": f"msgraph://servicePrincipals/{sp_id}",
            "data": sp_data,
            "metadata": {
                "description": f"Service principal information for {sp_id}",
                "lastUpdated": str(None)
            }
        }
    
    async def _get_specific_directory_role_resource(self, path: str, select_param: Optional[str]) -> Dict[str, Any]:
        """Get specific directory role resource."""
        parts = path.split("/")
        role_id = parts[1]
        
        if len(parts) > 2 and parts[2] == "members":
            # Get role members
            query_params = {}
            if select_param:
                query_params["$select"] = select_param
            
            members_data = await self.graph_client.get(f"directoryRoles/{role_id}/members", query_params)
            
            return {
                "type": "collection",
                "source": f"msgraph://directoryRoles/{role_id}/members",
                "data": members_data,
                "metadata": {
                    "description": f"Members of directory role {role_id}",
                    "itemType": "user",
                    "count": len(members_data.get("value", [])),
                    "hasMore": "@odata.nextLink" in members_data,
                    "lastUpdated": str(None)
                }
            }
        else:
            # Get role info
            query_params = {}
            if select_param:
                query_params["$select"] = select_param
            
            role_data = await self.graph_client.get(f"directoryRoles/{role_id}", query_params)
            
            return {
                "type": "directoryRole",
                "source": f"msgraph://directoryRoles/{role_id}",
                "data": role_data,
                "metadata": {
                    "description": f"Directory role information for {role_id}",
                    "lastUpdated": str(None)
                }
            }