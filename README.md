# Microsoft Graph MCP Server

A comprehensive Model Context Protocol (MCP) server implementation for Microsoft Graph v2 beta API. This server enables AI applications to interact with Microsoft 365 and Azure AD services through standardized MCP interfaces.

## Features

### Core Capabilities
- **Multiple Authentication Methods**: Client credentials, device code, interactive browser, managed identity, Azure CLI
- **Comprehensive API Coverage**: Users, groups, applications, directory roles, and organizational data
- **Production Ready**: Rate limiting, retry logic, error handling, and async operations
- **Configurable**: Extensive configuration options with environment variable support
- **Secure**: Token caching, SSL validation, and permission-based access control

### MCP Interfaces

#### Tools (Direct Operations)
- **User Management**: List, get, create, update, delete users
- **Group Management**: List groups, manage members, get group details
- **Application Management**: List applications and service principals
- **Directory Operations**: Get organization info, directory roles, and role members
- **Utility Tools**: Connection testing, service information

#### Resources (Structured Data Access)
- **Static Resources**: Current user profile, organization info, service metadata
- **Collections**: Users, groups, applications with pagination support
- **Schemas**: Object type definitions for understanding data structures
- **Dynamic Resources**: Specific users/groups/applications by ID with URI-based access

#### Prompts (AI Workflows)
- **Security Analysis**: User profiles, permissions, application security reviews
- **Management Workflows**: User lifecycle, group membership analysis, role assignments
- **Reporting**: Inactive users, organizational health checks, compliance reviews

## Installation

### Prerequisites
- Python 3.10 or higher
- Azure AD application registration with appropriate permissions
- Microsoft 365 or Azure AD tenant access

### Install from Source

```bash
# Clone the repository
git clone <repository-url>
cd msgraph-mcp

# Install in development mode
pip install -e .

# Or install directly
pip install .
```

### Install Development Dependencies

```bash
# Install with development dependencies
pip install -e ".[dev]"
```

## Configuration

### Environment Variables

The server can be configured using environment variables with the `MSGRAPH_` prefix:

```bash
# Required for most authentication methods
export MSGRAPH_TENANT_ID="your-tenant-id"
export MSGRAPH_CLIENT_ID="your-client-id"
export MSGRAPH_CLIENT_SECRET="your-client-secret"

# Optional configuration
export MSGRAPH_AUTH_METHOD="client_credentials"  # default
export MSGRAPH_LOG_LEVEL="INFO"
export MSGRAPH_MAX_REQUESTS_PER_SECOND="10"
export MSGRAPH_ENABLE_USER_OPERATIONS="true"
export MSGRAPH_ENABLE_GROUP_OPERATIONS="true"
```

### Configuration File

Create a `.env` file in your working directory:

```env
# Azure AD Configuration
MSGRAPH_TENANT_ID=your-tenant-id
MSGRAPH_CLIENT_ID=your-application-client-id
MSGRAPH_CLIENT_SECRET=your-client-secret
MSGRAPH_AUTH_METHOD=client_credentials

# API Configuration
MSGRAPH_GRAPH_BASE_URL=https://graph.microsoft.com/beta
MSGRAPH_MAX_REQUESTS_PER_SECOND=10
MSGRAPH_REQUEST_TIMEOUT=30

# Feature Toggles
MSGRAPH_ENABLE_USER_OPERATIONS=true
MSGRAPH_ENABLE_GROUP_OPERATIONS=true
MSGRAPH_ENABLE_APPLICATION_OPERATIONS=true
MSGRAPH_ENABLE_DIRECTORY_OPERATIONS=true
MSGRAPH_ENABLE_MAIL_OPERATIONS=false
MSGRAPH_ENABLE_CALENDAR_OPERATIONS=false
MSGRAPH_ENABLE_TEAMS_OPERATIONS=false

# Logging
MSGRAPH_LOG_LEVEL=INFO
MSGRAPH_ENABLE_DEBUG_LOGGING=false
```

### Authentication Methods

#### 1. Client Credentials (Service-to-Service)
```bash
export MSGRAPH_AUTH_METHOD="client_credentials"
export MSGRAPH_TENANT_ID="your-tenant-id"
export MSGRAPH_CLIENT_ID="your-client-id"
export MSGRAPH_CLIENT_SECRET="your-client-secret"
```

#### 2. Device Code Flow
```bash
export MSGRAPH_AUTH_METHOD="device_code"
export MSGRAPH_TENANT_ID="your-tenant-id"
export MSGRAPH_CLIENT_ID="your-client-id"
```

#### 3. Interactive Browser
```bash
export MSGRAPH_AUTH_METHOD="interactive"
export MSGRAPH_TENANT_ID="your-tenant-id"
export MSGRAPH_CLIENT_ID="your-client-id"
```

#### 4. Managed Identity (Azure)
```bash
export MSGRAPH_AUTH_METHOD="managed_identity"
# No additional configuration needed when running on Azure
```

#### 5. Azure CLI
```bash
export MSGRAPH_AUTH_METHOD="azure_cli"
# Requires 'az login' to be completed
```

## Usage

### Command Line Interface

```bash
# Start the MCP server
msgraph-mcp

# Test configuration and connection
msgraph-mcp --test-config

# Run with debug logging
msgraph-mcp --log-level DEBUG --debug

# Use custom configuration file
msgraph-mcp --config-file /path/to/custom.env
```

### Programmatic Usage

```python
import asyncio
from msgraph_mcp import MCPGraphServer, GraphConfig

async def main():
    # Create configuration
    config = GraphConfig(
        tenant_id="your-tenant-id",
        client_id="your-client-id",
        client_secret="your-client-secret",
        auth_method="client_credentials"
    )
    
    # Create and run server
    server = MCPGraphServer(config)
    await server.run()

if __name__ == "__main__":
    asyncio.run(main())
```

### Integration with MCP Clients

The server implements the standard MCP protocol and can be used with any MCP-compatible client:

```json
{
  "mcpServers": {
    "msgraph": {
      "command": "msgraph-mcp",
      "env": {
        "MSGRAPH_TENANT_ID": "your-tenant-id",
        "MSGRAPH_CLIENT_ID": "your-client-id",
        "MSGRAPH_CLIENT_SECRET": "your-client-secret"
      }
    }
  }
}
```

## Azure AD Application Setup

### Required Permissions

Your Azure AD application needs the following Microsoft Graph permissions:

#### Application Permissions (for service-to-service scenarios)
- `User.Read.All` - Read all user profiles
- `Group.Read.All` - Read all groups
- `Application.Read.All` - Read all applications
- `Directory.Read.All` - Read directory data
- `Organization.Read.All` - Read organization information

#### Delegated Permissions (for user-context scenarios)
- `User.Read` - Read user profile
- `User.ReadWrite.All` - Read and write all user profiles
- `Group.ReadWrite.All` - Read and write all groups
- `Directory.AccessAsUser.All` - Access directory as user

### Grant Admin Consent

After configuring permissions, ensure admin consent is granted for your tenant.

## API Examples

### Using Tools

```python
# List users
result = await server.call_tool("list_users", {
    "top": 10,
    "select": "displayName,mail,jobTitle"
})

# Get specific user
result = await server.call_tool("get_user", {
    "user_id": "user@company.com",
    "select": "displayName,mail,department"
})

# Create user
result = await server.call_tool("create_user", {
    "display_name": "John Doe",
    "user_principal_name": "john.doe@company.com",
    "mail_nickname": "johndoe",
    "password": "TempPassword123!"
})
```

### Using Resources

```python
# Get current user profile
profile = await server.get_resource("msgraph://me")

# Get users collection
users = await server.get_resource("msgraph://users?top=50&select=displayName,mail")

# Get specific group members
members = await server.get_resource("msgraph://groups/group-id/members")
```

### Using Prompts

```python
# Analyze user profile for security issues
analysis = await server.get_prompt("analyze_user_profile", {
    "user_id": "user@company.com"
})

# Generate inactive users report
report = await server.get_prompt("inactive_users_report", {
    "days_threshold": "90"
})
```

## Development

### Project Structure

```
src/msgraph_mcp/
├── __init__.py          # Package initialization
├── __main__.py          # CLI entry point
├── server.py            # Main MCP server implementation
├── config.py            # Configuration management
├── auth.py              # Authentication handling
├── graph_client.py      # Microsoft Graph client
├── tools.py             # MCP tools implementation
├── resources.py         # MCP resources implementation
└── prompts.py           # MCP prompts implementation
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=msgraph_mcp

# Run specific test file
pytest tests/test_server.py
```

### Code Quality

```bash
# Format code
black src/ tests/

# Lint code
ruff check src/ tests/

# Type checking
mypy src/
```

## Security Considerations

1. **Credential Management**: Never commit secrets to version control
2. **Least Privilege**: Only enable required feature toggles and permissions
3. **Network Security**: Use SSL validation in production
4. **Token Security**: Tokens are cached securely and refreshed automatically
5. **Rate Limiting**: Built-in rate limiting prevents API abuse

## Troubleshooting

### Common Issues

#### Authentication Errors
```bash
# Test your configuration
msgraph-mcp --test-config

# Check Azure AD app permissions and admin consent
# Verify tenant ID, client ID, and client secret
```

#### Permission Errors
```bash
# Verify your app has the required Microsoft Graph permissions
# Ensure admin consent has been granted
# Check that feature toggles match your permissions
```

#### Rate Limiting
```bash
# Adjust rate limiting settings
export MSGRAPH_MAX_REQUESTS_PER_SECOND=5
export MSGRAPH_MAX_CONCURRENT_REQUESTS=3
```

### Debug Logging

Enable debug logging to troubleshoot issues:

```bash
msgraph-mcp --log-level DEBUG --debug
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

## License

MIT License - see LICENSE file for details.

## Support

For issues and questions:
1. Check the troubleshooting section
2. Review Microsoft Graph documentation
3. Open an issue on the repository
4. Check Azure AD application configuration

---

**Note**: This implementation uses Microsoft Graph v2 beta endpoints. Some features may change or require different permissions as Microsoft updates their API.
