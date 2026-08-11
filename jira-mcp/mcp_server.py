"""
Jira MCP Server - Entry Point

A Model Context Protocol server for Jira integration.
Provides issue management, hierarchy traversal, sprint management, and more.
"""
import logging

from fastapi import FastAPI
from fastapi_mcp import FastApiMCP

from config import MCP_TRANSPORT
from routes import register_routes

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI application
app = FastAPI(
    title="Jira MCP Server",
    description="MCP server for Jira integration with issue management, "
                "hierarchy traversal, sprint operations, and attachment handling.",
    version="2.0.0"
)

# Register all route modules
register_routes(app)

# Mount MCP protocol
mcp = FastApiMCP(app)
if MCP_TRANSPORT == "stdio":
    mcp.mount()  # Use stdio transport (e.g. for VS Code Copilot)
else:
    mcp.mount_http()  # Use HTTP transport (default, e.g. for Claude Code)
