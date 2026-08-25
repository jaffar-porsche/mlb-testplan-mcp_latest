# workspace

Concise agent instructions. Full context: `AGENTS.md`.

## Repository summary

- Languages: Python, Markdown, Shell, JSON, Batch

## High-level details

- `.` — A FastAPI-based xRay test-plan MCP server that proxies to the xRay v2 API to build a FAIL test report with KPM IDs, handling both Test Plan and single Test issue types.
- `jira-mcp` — Entry point for a Jira MCP server (FastAPI + FastApiMCP) that registers route modules for issue management, hierarchy traversal, and sprint operations.
- `jira-mcp/routes` — Defines FastAPI routes for Jira issue CRUD, search, hierarchy and roadmap endpoints, built on top of the jira client and hierarchy utilities.
- `jira-mcp/utils` — Provides utility functions to recursively traverse Jira Epic/Feature/Story issue hierarchies and build markdown hierarchy trees and PI-based roadmaps.
- `jira-mcp/tests` — Pytest test suite verifying that all Jira MCP route modules import correctly and expose their expected endpoint paths.
- `confluence-mcp` — Entry point for a Confluence MCP server (FastAPI + FastApiMCP) that registers route modules for page management, search, hierarchy traversal, and comments.
- `confluence-mcp/routes` — Implements Confluence page CRUD endpoints (create, get, update, move, delete, including cascading delete of descendant pages) via the confluence client.
- `confluence-mcp/integration` — Provides client integration templates and configs (Claude Desktop config, VS Code/Copilot prompts, Postman collection, HTTP request files) for connecting external MCP clients to the Confluence MCP server.

## Build & test

- `pip install -r requirements.txt` — Install root server dependencies
- `pip install -r jira-mcp/requirements.txt` — Install jira-mcp dependencies
- `pip install -r confluence-mcp/requirements.txt` — Install confluence-mcp dependencies
- `cd jira-mcp && pytest` — Run jira-mcp tests
- `cd confluence-mcp && pytest` — Run confluence-mcp tests
- `uvicorn server:app --host 0.0.0.0 --port 8080` — Run root MCP server

## Layout & architecture

- Each MCP subproject (root mlb-testplan-mcp, jira-mcp, confluence-mcp) is built as an independent FastAPI + fastapi_mcp application with its own entrypoint, requirements file, Dockerfile, and port, and can be run and deployed standalone.
- jira-mcp and confluence-mcp validate required credentials (JIRA_PAT / CONFLUENCE_PAT) at module import time in config.py by raising RuntimeError, so any code path that imports config (server startup, tests, tooling) fails immediately if the PAT env var is missing rather than failing lazily on first API call.
- In jira-mcp and confluence-mcp, every FastAPI route handler body is wrapped in try/except Exception and converted into an HTTPException with an explanatory detail message; no route lets a raw exception propagate to the client.
- All routers in jira-mcp and confluence-mcp are registered exclusively through a single routes/__init__.py::register_routes(app) function called from the service's mcp_server.py; there is no ad-hoc app.include_router() call elsewhere in the codebase.
- Shared xRay v2 API interaction logic (error handling, response passthrough, pagination, field extraction) is centralized in utils/xray helper functions rather than reimplemented in each route/report-building function of the root server.
- For MLB test-plan failure-analysis workflows, agents are constrained to use only the mlb-testplan MCP tools and are prohibited from invoking the separate Jira MCP, Confluence MCP, or GitLab MCP servers, keeping the three MCP services logically isolated at the agent-orchestration layer despite being co-located in one repository.

## Conventions and do-nots

- Each MCP service (jira-mcp, confluence-mcp) organizes FastAPI endpoints into per-domain modules under a routes/ package, with a routes/__init__.py exposing a register_routes(app) function that includes each router.
- Route handler bodies wrap their logic in try/except Exception blocks and convert failures into fastapi.HTTPException with an explanatory detail message.
- Each route function is decorated with @router.<method>(path, summary=..., operation_id=...) and includes a docstring describing parameters, matching the FastAPI-MCP tool-description convention.
- Tests are organized into pytest classes grouped by endpoint area (e.g. TestHealthEndpoints, TestPageEndpoints) using a shared 'client' fixture and mocked service clients (e.g. mock_confluence).
- Each module obtains its own logger via logger = logging.getLogger(__name__) immediately after imports.
- Module-level private helper functions used only within a route file are prefixed with a single underscore (e.g. _find_epic_link_field, _resolve_version_names).
- Each source file starts with a module-level docstring summarizing its purpose, followed by stdlib imports, then third-party imports, then local imports.
