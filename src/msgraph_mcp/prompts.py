"""
MCP Prompts implementation for Microsoft Graph.
"""

import json
import logging
from typing import Any, Dict, List, Optional

from mcp.types import Prompt, PromptMessage, TextContent, ImageContent, EmbeddedResource
import mcp.types as types

from .config import GraphConfig
from .graph_client import GraphClient, GraphAPIError

logger = logging.getLogger(__name__)


class GraphPromptsHandler:
    """Handler for Microsoft Graph MCP prompts."""
    
    def __init__(self, config: GraphConfig, graph_client: GraphClient):
        """Initialize the prompts handler."""
        self.config = config
        self.graph_client = graph_client
        self.prompts = self._define_prompts()
        
        logger.info(f"Graph prompts handler initialized with {len(self.prompts)} prompts")
    
    def _define_prompts(self) -> List[Prompt]:
        """Define available prompts based on configuration."""
        prompts = []
        
        # Core prompts (always available)
        prompts.extend([
            Prompt(
                name="analyze_user_profile",
                description="Analyze a user's profile and provide insights",
                arguments=[
                    types.PromptArgument(
                        name="user_id",
                        description="User ID or user principal name to analyze",
                        required=True
                    ),
                    types.PromptArgument(
                        name="include_groups",
                        description="Include group memberships in analysis",
                        required=False
                    )
                ]
            ),
            Prompt(
                name="security_assessment",
                description="Perform a security assessment of the organization",
                arguments=[
                    types.PromptArgument(
                        name="scope",
                        description="Scope of assessment (users, groups, applications, all)",
                        required=False
                    )
                ]
            ),
            Prompt(
                name="onboarding_checklist",
                description="Generate an onboarding checklist for a new user",
                arguments=[
                    types.PromptArgument(
                        name="user_id",
                        description="User ID of the new user",
                        required=True
                    ),
                    types.PromptArgument(
                        name="role",
                        description="Role or job title of the new user",
                        required=False
                    )
                ]
            ),
            Prompt(
                name="permission_review",
                description="Review and analyze permissions for a user or application",
                arguments=[
                    types.PromptArgument(
                        name="target_type",
                        description="Type of target to review (user, application, group)",
                        required=True
                    ),
                    types.PromptArgument(
                        name="target_id",
                        description="ID of the target to review",
                        required=True
                    )
                ]
            )
        ])
        
        # User management prompts
        if self.config.enable_user_operations:
            prompts.extend([
                Prompt(
                    name="user_lifecycle_summary",
                    description="Generate a comprehensive summary of user lifecycle events",
                    arguments=[
                        types.PromptArgument(
                            name="user_id",
                            description="User ID to analyze",
                            required=True
                        ),
                        types.PromptArgument(
                            name="include_signin_activity",
                            description="Include sign-in activity analysis",
                            required=False
                        )
                    ]
                ),
                Prompt(
                    name="inactive_users_report",
                    description="Generate a report of inactive users",
                    arguments=[
                        types.PromptArgument(
                            name="days_threshold",
                            description="Number of days to consider as inactive",
                            required=False
                        ),
                        types.PromptArgument(
                            name="include_guests",
                            description="Include guest users in the report",
                            required=False
                        )
                    ]
                ),
                Prompt(
                    name="bulk_user_operations",
                    description="Guide for performing bulk operations on users",
                    arguments=[
                        types.PromptArgument(
                            name="operation_type",
                            description="Type of bulk operation (create, update, disable, delete)",
                            required=True
                        ),
                        types.PromptArgument(
                            name="user_count",
                            description="Estimated number of users to process",
                            required=False
                        )
                    ]
                )
            ])
        
        # Group management prompts
        if self.config.enable_group_operations:
            prompts.extend([
                Prompt(
                    name="group_membership_analysis",
                    description="Analyze group memberships and identify patterns",
                    arguments=[
                        types.PromptArgument(
                            name="group_id",
                            description="Specific group ID to analyze (optional)",
                            required=False
                        ),
                        types.PromptArgument(
                            name="analysis_type",
                            description="Type of analysis (membership_overlap, orphaned_groups, large_groups)",
                            required=False
                        )
                    ]
                ),
                Prompt(
                    name="access_control_review",
                    description="Review access control through group memberships",
                    arguments=[
                        types.PromptArgument(
                            name="department",
                            description="Department to focus the review on",
                            required=False
                        ),
                        types.PromptArgument(
                            name="include_nested_groups",
                            description="Include nested group memberships",
                            required=False
                        )
                    ]
                )
            ])
        
        # Application management prompts
        if self.config.enable_application_operations:
            prompts.extend([
                Prompt(
                    name="app_security_review",
                    description="Security review of applications and service principals",
                    arguments=[
                        types.PromptArgument(
                            name="app_type",
                            description="Type of applications to review (all, multi_tenant, single_tenant)",
                            required=False
                        ),
                        types.PromptArgument(
                            name="risk_level",
                            description="Focus on specific risk level (high, medium, low)",
                            required=False
                        )
                    ]
                ),
                Prompt(
                    name="oauth_consent_analysis",
                    description="Analyze OAuth consent grants and permissions",
                    arguments=[
                        types.PromptArgument(
                            name="consent_type",
                            description="Type of consent to analyze (admin, user, all)",
                            required=False
                        )
                    ]
                )
            ])
        
        # Directory management prompts
        if self.config.enable_directory_operations:
            prompts.extend([
                Prompt(
                    name="role_assignment_review",
                    description="Review directory role assignments",
                    arguments=[
                        types.PromptArgument(
                            name="role_name",
                            description="Specific role to review (optional)",
                            required=False
                        ),
                        types.PromptArgument(
                            name="privileged_only",
                            description="Focus only on privileged roles",
                            required=False
                        )
                    ]
                ),
                Prompt(
                    name="organization_health_check",
                    description="Comprehensive health check of the organization",
                    arguments=[
                        types.PromptArgument(
                            name="focus_areas",
                            description="Specific areas to focus on (security, compliance, performance)",
                            required=False
                        )
                    ]
                )
            ])
        
        return prompts
    
    async def list_prompts(self) -> List[Prompt]:
        """List all available prompts."""
        return self.prompts
    
    async def get_prompt(self, name: str, arguments: Dict[str, str]) -> types.GetPromptResult:
        """Get a specific prompt with the given arguments."""
        try:
            logger.debug(f"Getting prompt: {name} with arguments: {arguments}")
            
            # Route to appropriate handler
            if name == "analyze_user_profile":
                messages = await self._analyze_user_profile_prompt(arguments)
            elif name == "security_assessment":
                messages = await self._security_assessment_prompt(arguments)
            elif name == "onboarding_checklist":
                messages = await self._onboarding_checklist_prompt(arguments)
            elif name == "permission_review":
                messages = await self._permission_review_prompt(arguments)
            elif name == "user_lifecycle_summary":
                messages = await self._user_lifecycle_summary_prompt(arguments)
            elif name == "inactive_users_report":
                messages = await self._inactive_users_report_prompt(arguments)
            elif name == "bulk_user_operations":
                messages = await self._bulk_user_operations_prompt(arguments)
            elif name == "group_membership_analysis":
                messages = await self._group_membership_analysis_prompt(arguments)
            elif name == "access_control_review":
                messages = await self._access_control_review_prompt(arguments)
            elif name == "app_security_review":
                messages = await self._app_security_review_prompt(arguments)
            elif name == "oauth_consent_analysis":
                messages = await self._oauth_consent_analysis_prompt(arguments)
            elif name == "role_assignment_review":
                messages = await self._role_assignment_review_prompt(arguments)
            elif name == "organization_health_check":
                messages = await self._organization_health_check_prompt(arguments)
            else:
                raise ValueError(f"Unknown prompt: {name}")
            
            return types.GetPromptResult(
                description=f"Generated prompt for {name}",
                messages=messages
            )
            
        except Exception as e:
            logger.error(f"Error getting prompt {name}: {e}")
            error_message = types.PromptMessage(
                role="system",
                content=types.TextContent(
                    type="text",
                    text=f"Error generating prompt '{name}': {str(e)}"
                )
            )
            return types.GetPromptResult(
                description=f"Error generating prompt for {name}",
                messages=[error_message]
            )
    
    # Prompt implementations
    async def _analyze_user_profile_prompt(self, args: Dict[str, str]) -> List[types.PromptMessage]:
        """Generate user profile analysis prompt."""
        user_id = args.get("user_id", "")
        include_groups = args.get("include_groups", "false").lower() == "true"
        
        try:
            # Fetch user data
            user_data = await self.graph_client.get(f"users/{user_id}")
            
            # Optionally fetch group memberships
            groups_text = ""
            if include_groups:
                try:
                    groups_data = await self.graph_client.get(f"users/{user_id}/memberOf")
                    groups = groups_data.get("value", [])
                    if groups:
                        group_names = [g.get("displayName", "Unknown") for g in groups]
                        groups_text = f"\n\nGroup Memberships:\n" + "\n".join(f"- {name}" for name in group_names)
                except Exception:
                    groups_text = "\n\nGroup Memberships: Unable to retrieve"
            
            user_info = f"""
User Profile Analysis for: {user_data.get('displayName', 'Unknown')}
User Principal Name: {user_data.get('userPrincipalName', 'N/A')}
Email: {user_data.get('mail', 'N/A')}
Job Title: {user_data.get('jobTitle', 'N/A')}
Department: {user_data.get('department', 'N/A')}
Office Location: {user_data.get('officeLocation', 'N/A')}
Account Enabled: {user_data.get('accountEnabled', 'N/A')}
Created: {user_data.get('createdDateTime', 'N/A')}
Last Sign-in: {user_data.get('lastSignInDateTime', 'N/A')}{groups_text}
            """.strip()
            
        except Exception as e:
            user_info = f"Error retrieving user data for {user_id}: {str(e)}"
        
        return [
            types.PromptMessage(
                role="system",
                content=types.TextContent(
                    type="text",
                    text="You are an IT administrator analyzing a user profile. Provide insights about security, access patterns, and potential issues."
                )
            ),
            types.PromptMessage(
                role="user",
                content=types.TextContent(
                    type="text",
                    text=f"Please analyze the following user profile and provide insights:\n\n{user_info}"
                )
            )
        ]
    
    async def _security_assessment_prompt(self, args: Dict[str, str]) -> List[types.PromptMessage]:
        """Generate security assessment prompt."""
        scope = args.get("scope", "all")
        
        assessment_data = []
        
        try:
            if scope in ["users", "all"]:
                # Get sample of users
                users_data = await self.graph_client.get("users", {"$top": "10", "$select": "displayName,accountEnabled,lastSignInDateTime,createdDateTime"})
                users_count = len(users_data.get("value", []))
                assessment_data.append(f"Users: {users_count} users retrieved for analysis")
            
            if scope in ["groups", "all"]:
                # Get sample of groups
                groups_data = await self.graph_client.get("groups", {"$top": "10", "$select": "displayName,securityEnabled,mailEnabled"})
                groups_count = len(groups_data.get("value", []))
                assessment_data.append(f"Groups: {groups_count} groups retrieved for analysis")
            
            if scope in ["applications", "all"]:
                # Get sample of applications
                apps_data = await self.graph_client.get("applications", {"$top": "10", "$select": "displayName,signInAudience,createdDateTime"})
                apps_count = len(apps_data.get("value", []))
                assessment_data.append(f"Applications: {apps_count} applications retrieved for analysis")
            
        except Exception as e:
            assessment_data.append(f"Error retrieving data: {str(e)}")
        
        data_summary = "\n".join(assessment_data)
        
        return [
            types.PromptMessage(
                role="system",
                content=types.TextContent(
                    type="text",
                    text="You are a security analyst performing a comprehensive security assessment of an organization's Microsoft 365 environment. Focus on identifying security risks, compliance issues, and recommendations."
                )
            ),
            types.PromptMessage(
                role="user",
                content=types.TextContent(
                    type="text",
                    text=f"Please perform a security assessment based on the following organizational data:\n\nScope: {scope}\n\nData Summary:\n{data_summary}\n\nProvide a detailed security assessment with recommendations."
                )
            )
        ]
    
    async def _onboarding_checklist_prompt(self, args: Dict[str, str]) -> List[types.PromptMessage]:
        """Generate onboarding checklist prompt."""
        user_id = args.get("user_id", "")
        role = args.get("role", "")
        
        try:
            # Get user information
            user_data = await self.graph_client.get(f"users/{user_id}")
            user_info = f"""
New User: {user_data.get('displayName', 'Unknown')}
Email: {user_data.get('userPrincipalName', 'N/A')}
Job Title: {user_data.get('jobTitle', role or 'N/A')}
Department: {user_data.get('department', 'N/A')}
Account Status: {user_data.get('accountEnabled', 'N/A')}
            """.strip()
        except Exception as e:
            user_info = f"Error retrieving user data: {str(e)}"
        
        return [
            types.PromptMessage(
                role="system",
                content=types.TextContent(
                    type="text",
                    text="You are an IT administrator creating an onboarding checklist for a new employee. Create a comprehensive checklist that covers account setup, access provisioning, security requirements, and training needs."
                )
            ),
            types.PromptMessage(
                role="user",
                content=types.TextContent(
                    type="text",
                    text=f"Please create an onboarding checklist for the following new user:\n\n{user_info}\n\nInclude all necessary steps for account setup, access provisioning, and security compliance."
                )
            )
        ]
    
    async def _permission_review_prompt(self, args: Dict[str, str]) -> List[types.PromptMessage]:
        """Generate permission review prompt."""
        target_type = args.get("target_type", "")
        target_id = args.get("target_id", "")
        
        try:
            if target_type == "user":
                # Get user and their group memberships
                user_data = await self.graph_client.get(f"users/{target_id}")
                groups_data = await self.graph_client.get(f"users/{target_id}/memberOf")
                
                target_info = f"""
User: {user_data.get('displayName', 'Unknown')} ({user_data.get('userPrincipalName', 'N/A')})
Job Title: {user_data.get('jobTitle', 'N/A')}
Department: {user_data.get('department', 'N/A')}

Group Memberships:
"""
                groups = groups_data.get("value", [])
                for group in groups[:10]:  # Limit to first 10 groups
                    target_info += f"- {group.get('displayName', 'Unknown')}\n"
                
            elif target_type == "application":
                # Get application data
                app_data = await self.graph_client.get(f"applications/{target_id}")
                target_info = f"""
Application: {app_data.get('displayName', 'Unknown')}
App ID: {app_data.get('appId', 'N/A')}
Sign-in Audience: {app_data.get('signInAudience', 'N/A')}
Created: {app_data.get('createdDateTime', 'N/A')}
                """.strip()
                
            elif target_type == "group":
                # Get group data and members
                group_data = await self.graph_client.get(f"groups/{target_id}")
                members_data = await self.graph_client.get(f"groups/{target_id}/members", {"$top": "10"})
                
                target_info = f"""
Group: {group_data.get('displayName', 'Unknown')}
Description: {group_data.get('description', 'N/A')}
Security Enabled: {group_data.get('securityEnabled', 'N/A')}
Mail Enabled: {group_data.get('mailEnabled', 'N/A')}

Members (first 10):
"""
                members = members_data.get("value", [])
                for member in members:
                    target_info += f"- {member.get('displayName', 'Unknown')}\n"
            else:
                target_info = f"Invalid target type: {target_type}"
                
        except Exception as e:
            target_info = f"Error retrieving data for {target_type} {target_id}: {str(e)}"
        
        return [
            types.PromptMessage(
                role="system",
                content=types.TextContent(
                    type="text",
                    text="You are a security auditor reviewing permissions and access rights. Analyze the provided information and identify any security concerns, excessive permissions, or compliance issues."
                )
            ),
            types.PromptMessage(
                role="user",
                content=types.TextContent(
                    type="text",
                    text=f"Please review the permissions and access rights for the following {target_type}:\n\n{target_info}\n\nProvide a security assessment and recommendations."
                )
            )
        ]
    
    async def _user_lifecycle_summary_prompt(self, args: Dict[str, str]) -> List[types.PromptMessage]:
        """Generate user lifecycle summary prompt."""
        user_id = args.get("user_id", "")
        include_signin = args.get("include_signin_activity", "false").lower() == "true"
        
        try:
            user_data = await self.graph_client.get(f"users/{user_id}")
            
            lifecycle_info = f"""
User: {user_data.get('displayName', 'Unknown')}
Account Created: {user_data.get('createdDateTime', 'N/A')}
Account Enabled: {user_data.get('accountEnabled', 'N/A')}
Last Password Change: {user_data.get('lastPasswordChangeDateTime', 'N/A')}
"""
            
            if include_signin:
                signin_info = f"Last Sign-in: {user_data.get('lastSignInDateTime', 'N/A')}"
                lifecycle_info += signin_info
                
        except Exception as e:
            lifecycle_info = f"Error retrieving user lifecycle data: {str(e)}"
        
        return [
            types.PromptMessage(
                role="system",
                content=types.TextContent(
                    type="text",
                    text="You are an IT administrator analyzing user lifecycle events. Provide insights about account activity, potential issues, and recommendations for account management."
                )
            ),
            types.PromptMessage(
                role="user",
                content=types.TextContent(
                    type="text",
                    text=f"Please analyze the following user lifecycle information:\n\n{lifecycle_info}\n\nProvide insights and recommendations."
                )
            )
        ]
    
    async def _inactive_users_report_prompt(self, args: Dict[str, str]) -> List[types.PromptMessage]:
        """Generate inactive users report prompt."""
        days_threshold = args.get("days_threshold", "90")
        include_guests = args.get("include_guests", "false").lower() == "true"
        
        # This is a simplified implementation - in a real scenario, you'd implement
        # more sophisticated filtering based on sign-in activity
        try:
            query_params = {"$top": "50", "$select": "displayName,userPrincipalName,lastSignInDateTime,userType,accountEnabled"}
            if not include_guests:
                query_params["$filter"] = "userType eq 'Member'"
            
            users_data = await self.graph_client.get("users", query_params)
            users_count = len(users_data.get("value", []))
            
            report_info = f"""
Inactive Users Analysis (Threshold: {days_threshold} days)
Include Guest Users: {include_guests}
Sample Size: {users_count} users analyzed

Note: This is a sample analysis. Full implementation would require detailed sign-in activity filtering.
            """.strip()
            
        except Exception as e:
            report_info = f"Error generating inactive users report: {str(e)}"
        
        return [
            types.PromptMessage(
                role="system",
                content=types.TextContent(
                    type="text",
                    text="You are an IT administrator generating a report on inactive users. Analyze the data and provide recommendations for account cleanup and security improvements."
                )
            ),
            types.PromptMessage(
                role="user",
                content=types.TextContent(
                    type="text",
                    text=f"Please analyze the following inactive users data and generate a comprehensive report:\n\n{report_info}"
                )
            )
        ]
    
    async def _bulk_user_operations_prompt(self, args: Dict[str, str]) -> List[types.PromptMessage]:
        """Generate bulk user operations guide prompt."""
        operation_type = args.get("operation_type", "")
        user_count = args.get("user_count", "unknown")
        
        operation_info = f"""
Bulk Operation Type: {operation_type}
Estimated User Count: {user_count}

This guide will help you plan and execute bulk user operations safely and efficiently.
        """.strip()
        
        return [
            types.PromptMessage(
                role="system",
                content=types.TextContent(
                    type="text",
                    text="You are an expert IT administrator providing guidance on bulk user operations. Provide step-by-step instructions, best practices, and safety considerations."
                )
            ),
            types.PromptMessage(
                role="user",
                content=types.TextContent(
                    type="text",
                    text=f"Please provide a comprehensive guide for the following bulk operation:\n\n{operation_info}\n\nInclude best practices, safety measures, and step-by-step instructions."
                )
            )
        ]
    
    async def _group_membership_analysis_prompt(self, args: Dict[str, str]) -> List[types.PromptMessage]:
        """Generate group membership analysis prompt."""
        group_id = args.get("group_id", "")
        analysis_type = args.get("analysis_type", "general")
        
        try:
            if group_id:
                # Analyze specific group
                group_data = await self.graph_client.get(f"groups/{group_id}")
                members_data = await self.graph_client.get(f"groups/{group_id}/members", {"$top": "100"})
                
                analysis_info = f"""
Group Analysis: {group_data.get('displayName', 'Unknown')}
Group Type: {'Security' if group_data.get('securityEnabled') else 'Distribution'}
Member Count: {len(members_data.get('value', []))}
Description: {group_data.get('description', 'N/A')}
                """.strip()
            else:
                # General group analysis
                groups_data = await self.graph_client.get("groups", {"$top": "50"})
                groups_count = len(groups_data.get("value", []))
                
                analysis_info = f"""
Organization Group Analysis
Analysis Type: {analysis_type}
Sample Groups Analyzed: {groups_count}

This analysis covers group membership patterns across the organization.
                """.strip()
                
        except Exception as e:
            analysis_info = f"Error retrieving group data: {str(e)}"
        
        return [
            types.PromptMessage(
                role="system",
                content=types.TextContent(
                    type="text",
                    text="You are a security analyst analyzing group memberships and access patterns. Identify potential security risks, over-privileged accounts, and optimization opportunities."
                )
            ),
            types.PromptMessage(
                role="user",
                content=types.TextContent(
                    type="text",
                    text=f"Please analyze the following group membership data:\n\n{analysis_info}\n\nProvide insights on security, access patterns, and recommendations."
                )
            )
        ]
    
    async def _access_control_review_prompt(self, args: Dict[str, str]) -> List[types.PromptMessage]:
        """Generate access control review prompt."""
        department = args.get("department", "")
        include_nested = args.get("include_nested_groups", "false").lower() == "true"
        
        review_info = f"""
Access Control Review
Department Focus: {department or 'All Departments'}
Include Nested Groups: {include_nested}

This review will analyze access control through group memberships and permissions.
        """.strip()
        
        return [
            types.PromptMessage(
                role="system",
                content=types.TextContent(
                    type="text",
                    text="You are a compliance officer reviewing access controls. Analyze group-based permissions and identify any compliance issues or security concerns."
                )
            ),
            types.PromptMessage(
                role="user",
                content=types.TextContent(
                    type="text",
                    text=f"Please perform an access control review based on:\n\n{review_info}\n\nProvide compliance assessment and recommendations."
                )
            )
        ]
    
    async def _app_security_review_prompt(self, args: Dict[str, str]) -> List[types.PromptMessage]:
        """Generate application security review prompt."""
        app_type = args.get("app_type", "all")
        risk_level = args.get("risk_level", "all")
        
        try:
            # Get application data
            query_params = {"$top": "20", "$select": "displayName,signInAudience,publisherDomain,createdDateTime"}
            if app_type != "all":
                if app_type == "multi_tenant":
                    query_params["$filter"] = "signInAudience eq 'AzureADMultipleOrgs'"
                elif app_type == "single_tenant":
                    query_params["$filter"] = "signInAudience eq 'AzureADMyOrg'"
            
            apps_data = await self.graph_client.get("applications", query_params)
            apps_count = len(apps_data.get("value", []))
            
            review_info = f"""
Application Security Review
App Type Filter: {app_type}
Risk Level Focus: {risk_level}
Applications Analyzed: {apps_count}

This review covers application security posture and potential risks.
            """.strip()
            
        except Exception as e:
            review_info = f"Error retrieving application data: {str(e)}"
        
        return [
            types.PromptMessage(
                role="system",
                content=types.TextContent(
                    type="text",
                    text="You are a security architect reviewing application security. Analyze application configurations, permissions, and identify security risks."
                )
            ),
            types.PromptMessage(
                role="user",
                content=types.TextContent(
                    type="text",
                    text=f"Please perform an application security review:\n\n{review_info}\n\nProvide security assessment and recommendations."
                )
            )
        ]
    
    async def _oauth_consent_analysis_prompt(self, args: Dict[str, str]) -> List[types.PromptMessage]:
        """Generate OAuth consent analysis prompt."""
        consent_type = args.get("consent_type", "all")
        
        analysis_info = f"""
OAuth Consent Analysis
Consent Type Focus: {consent_type}

This analysis will review OAuth consent grants and application permissions.
        """.strip()
        
        return [
            types.PromptMessage(
                role="system",
                content=types.TextContent(
                    type="text",
                    text="You are a security analyst reviewing OAuth consent grants and application permissions. Identify risky permissions and unauthorized access."
                )
            ),
            types.PromptMessage(
                role="user",
                content=types.TextContent(
                    type="text",
                    text=f"Please analyze OAuth consent grants:\n\n{analysis_info}\n\nProvide security analysis and recommendations."
                )
            )
        ]
    
    async def _role_assignment_review_prompt(self, args: Dict[str, str]) -> List[types.PromptMessage]:
        """Generate role assignment review prompt."""
        role_name = args.get("role_name", "")
        privileged_only = args.get("privileged_only", "false").lower() == "true"
        
        try:
            # Get directory roles
            roles_data = await self.graph_client.get("directoryRoles")
            roles_count = len(roles_data.get("value", []))
            
            review_info = f"""
Directory Role Assignment Review
Specific Role: {role_name or 'All Roles'}
Privileged Roles Only: {privileged_only}
Total Roles: {roles_count}

This review analyzes directory role assignments and privilege escalation risks.
            """.strip()
            
        except Exception as e:
            review_info = f"Error retrieving role data: {str(e)}"
        
        return [
            types.PromptMessage(
                role="system",
                content=types.TextContent(
                    type="text",
                    text="You are a security auditor reviewing directory role assignments. Focus on privilege escalation risks and principle of least privilege."
                )
            ),
            types.PromptMessage(
                role="user",
                content=types.TextContent(
                    type="text",
                    text=f"Please review directory role assignments:\n\n{review_info}\n\nProvide security assessment and recommendations."
                )
            )
        ]
    
    async def _organization_health_check_prompt(self, args: Dict[str, str]) -> List[types.PromptMessage]:
        """Generate organization health check prompt."""
        focus_areas = args.get("focus_areas", "all")
        
        try:
            # Get organization data
            org_data = await self.graph_client.get("organization")
            org_info = org_data.get("value", [{}])[0] if org_data.get("value") else {}
            
            health_info = f"""
Organization Health Check
Organization: {org_info.get('displayName', 'Unknown')}
Focus Areas: {focus_areas}
Created: {org_info.get('createdDateTime', 'N/A')}

This comprehensive health check covers security, compliance, and operational aspects.
            """.strip()
            
        except Exception as e:
            health_info = f"Error retrieving organization data: {str(e)}"
        
        return [
            types.PromptMessage(
                role="system",
                content=types.TextContent(
                    type="text",
                    text="You are a senior IT consultant performing a comprehensive organization health check. Evaluate security posture, compliance status, and operational efficiency."
                )
            ),
            types.PromptMessage(
                role="user",
                content=types.TextContent(
                    type="text",
                    text=f"Please perform a comprehensive health check:\n\n{health_info}\n\nProvide detailed assessment and actionable recommendations."
                )
            )
        ]