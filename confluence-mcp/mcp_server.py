"""
Confluence MCP Server - Entry Point

A Model Context Protocol server for Confluence integration.
Provides page management, search, hierarchy traversal, comments, and more.
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
    title="Confluence MCP Server",
    description="MCP server for Confluence integration with page management, "
                "search, hierarchy traversal, and comment handling.",
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
