# Modules

- A FastAPI-based xRay test-plan MCP server that proxies to the xRay v2 API to build a FAIL test report with KPM IDs, handling both Test Plan and single Test issue types.
- Entry point for a Jira MCP server (FastAPI + FastApiMCP) that registers route modules for issue management, hierarchy traversal, and sprint operations.
- Defines FastAPI routes for Jira issue CRUD, search, hierarchy and roadmap endpoints, built on top of the jira client and hierarchy utilities.
- Provides utility functions to recursively traverse Jira Epic/Feature/Story issue hierarchies and build markdown hierarchy trees and PI-based roadmaps.
- Pytest test suite verifying that all Jira MCP route modules import correctly and expose their expected endpoint paths.
- Entry point for a Confluence MCP server (FastAPI + FastApiMCP) that registers route modules for page management, search, hierarchy traversal, and comments.
- Implements Confluence page CRUD endpoints (create, get, update, move, delete, including cascading delete of descendant pages) via the confluence client.
- Provides client integration templates and configs (Claude Desktop config, VS Code/Copilot prompts, Postman collection, HTTP request files) for connecting external MCP clients to the Confluence MCP server.
- Pytest test suite covering Confluence MCP endpoints, including health checks, using mocked Confluence client responses.
- Shared helper functions for proxying and interpreting xRay v2 API responses (error handling, response passthrough, test run/plan/exec retrieval, and payload field extraction) used across MCP routes.
