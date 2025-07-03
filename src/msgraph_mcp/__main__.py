#!/usr/bin/env python3
"""
Entry point for Microsoft Graph MCP Server.
"""

import asyncio
import argparse
import logging
import sys
from pathlib import Path

from .server import MCPGraphServer
from .config import load_config, GraphConfig


def setup_logging(level: str = "INFO", enable_debug: bool = False) -> None:
    """Set up logging configuration."""
    log_level = getattr(logging, level.upper(), logging.INFO)
    
    # Configure logging format
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # Configure root logger
    logging.basicConfig(
        level=log_level,
        format=log_format,
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    # Configure specific loggers
    if enable_debug:
        logging.getLogger("msgraph_mcp").setLevel(logging.DEBUG)
        logging.getLogger("httpx").setLevel(logging.INFO)
    else:
        logging.getLogger("httpx").setLevel(logging.WARNING)
        logging.getLogger("azure").setLevel(logging.WARNING)


def create_parser() -> argparse.ArgumentParser:
    """Create command line argument parser."""
    parser = argparse.ArgumentParser(
        prog="msgraph-mcp",
        description="Microsoft Graph MCP Server - Model Context Protocol server for Microsoft Graph v2 beta",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Run with default configuration
    msgraph-mcp

    # Run with custom log level
    msgraph-mcp --log-level DEBUG

    # Run with environment file
    MSGRAPH_TENANT_ID=your-tenant msgraph-mcp

    # Test configuration only
    msgraph-mcp --test-config

Environment Variables:
    MSGRAPH_TENANT_ID           Azure AD tenant ID
    MSGRAPH_CLIENT_ID           Azure AD application client ID
    MSGRAPH_CLIENT_SECRET       Azure AD application client secret
    MSGRAPH_AUTH_METHOD         Authentication method (client_credentials, device_code, etc.)
    MSGRAPH_LOG_LEVEL           Logging level (DEBUG, INFO, WARNING, ERROR)

For more configuration options, see the documentation.
        """
    )
    
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Set the logging level (default: INFO)"
    )
    
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging for Microsoft Graph requests"
    )
    
    parser.add_argument(
        "--config-file",
        type=Path,
        help="Path to configuration file (.env format)"
    )
    
    parser.add_argument(
        "--test-config",
        action="store_true",
        help="Test configuration and connection, then exit"
    )
    
    parser.add_argument(
        "--version",
        action="version",
        version="%(prog)s 0.1.0"
    )
    
    return parser


async def test_configuration(config: GraphConfig) -> bool:
    """Test the configuration by attempting to initialize and connect."""
    try:
        print("Testing Microsoft Graph MCP Server configuration...")
        print(f"Server: {config.server_name} v{config.server_version}")
        print(f"Graph URL: {config.graph_base_url}")
        print(f"Auth Method: {config.auth_method.value}")
        
        # Create and initialize server
        server = MCPGraphServer(config)
        await server.initialize()
        
        # Get server info
        info = server.get_server_info()
        print("\nServer Information:")
        for key, value in info.items():
            if key != "auth_info":  # Don't print sensitive auth info
                print(f"  {key}: {value}")
        
        print("\nConfiguration test successful! ✓")
        await server.cleanup()
        return True
        
    except Exception as e:
        print(f"\nConfiguration test failed: {e}")
        return False


async def main_async() -> int:
    """Main async function."""
    parser = create_parser()
    args = parser.parse_args()
    
    # Set up logging
    setup_logging(args.log_level, args.debug)
    logger = logging.getLogger(__name__)
    
    try:
        # Load configuration
        if args.config_file:
            # If config file specified, set environment variable for pydantic
            import os
            os.environ["MSGRAPH_ENV_FILE"] = str(args.config_file)
        
        config = load_config()
        
        # Override log level from config if specified in args
        if hasattr(config, 'log_level') and args.log_level != "INFO":
            config.log_level = args.log_level
            config.enable_debug_logging = args.debug
        
        # Test configuration if requested
        if args.test_config:
            success = await test_configuration(config)
            return 0 if success else 1
        
        # Create and run server
        logger.info("Starting Microsoft Graph MCP Server...")
        server = MCPGraphServer(config)
        await server.run()
        
        return 0
        
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
        return 0
    except Exception as e:
        logger.error(f"Server error: {e}")
        if args.debug:
            import traceback
            traceback.print_exc()
        return 1


def main() -> None:
    """Main entry point for the application."""
    try:
        exit_code = asyncio.run(main_async())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\nServer interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()