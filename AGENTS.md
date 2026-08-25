# workspace — Agent Context

## Repository Overview

- Primary languages: Python, Markdown, Shell, JSON, Batch
- Monorepo: yes
- OpenSpec: absent

## Modules

### mlb-testplan-mcp (root server)
- Path: `.`
- A FastAPI-based xRay test-plan MCP server that proxies to the xRay v2 API to build a FAIL test report with KPM IDs, handling both Test Plan and single Test issue types.
- Depends on: fastapi, fastapi_mcp, httpx, dotenv, bs4, pandas

### jira-mcp
- Path: `jira-mcp`
- Entry point for a Jira MCP server (FastAPI + FastApiMCP) that registers route modules for issue management, hierarchy traversal, and sprint operations.
- Public API: app
- Depends on: fastapi, fastapi_mcp

### jira-mcp-routes
- Path: `jira-mcp/routes`
- Defines FastAPI routes for Jira issue CRUD, search, hierarchy and roadmap endpoints, built on top of the jira client and hierarchy utilities.
- Public API: create_issue, get_issue, update_issue, search_issues, get_issue_hierarchy, get_issue_roadmap
- Depends on: fastapi

### jira-mcp-utils
- Path: `jira-mcp/utils`
- Provides utility functions to recursively traverse Jira Epic/Feature/Story issue hierarchies and build markdown hierarchy trees and PI-based roadmaps.
- Public API: HierarchyStats, get_issue_links, is_closed_status, get_child_issues, build_hierarchy_markdown, get_feature_with_versions, build_roadmap_markdown

### jira-mcp-tests
- Path: `jira-mcp/tests`
- Pytest test suite verifying that all Jira MCP route modules import correctly and expose their expected endpoint paths.
- Public API: test_routes_module_imports, test_issues_router_has_routes
- Depends on: pytest

### confluence-mcp
- Path: `confluence-mcp`
- Entry point for a Confluence MCP server (FastAPI + FastApiMCP) that registers route modules for page management, search, hierarchy traversal, and comments.
- Public API: app
- Depends on: fastapi, fastapi_mcp

### confluence-mcp-routes
- Path: `confluence-mcp/routes`
- Implements Confluence page CRUD endpoints (create, get, update, move, delete, including cascading delete of descendant pages) via the confluence client.
- Public API: create_page, create_page_simple, get_page, update_page, move_page, delete_page
- Depends on: fastapi

### confluence-mcp-integration
- Path: `confluence-mcp/integration`
- Provides client integration templates and configs (Claude Desktop config, VS Code/Copilot prompts, Postman collection, HTTP request files) for connecting external MCP clients to the Confluence MCP server.

### confluence-mcp-tests
- Path: `confluence-mcp/tests`
- Pytest test suite covering Confluence MCP endpoints, including health checks, using mocked Confluence client responses.
- Public API: TestHealthEndpoints
- Depends on: pytest

### utils
- Path: `utils`
- Shared helper functions for proxying and interpreting xRay v2 API responses (error handling, response passthrough, test run/plan/exec retrieval, and payload field extraction) used across MCP routes.
- Public API: raise_for_xray, proxy_response, request_xray, get_xray, get_testruns, get_testplan_tests, get_testexec_tests, build_step_fields, extract_items, get_jira_issue_metadata
- Depends on: fastapi

## Conventions

- [structure] Each MCP service (jira-mcp, confluence-mcp) organizes FastAPI endpoints into per-domain modules under a routes/ package, with a routes/__init__.py exposing a register_routes(app) function that includes each router.
- [style] Route handler bodies wrap their logic in try/except Exception blocks and convert failures into fastapi.HTTPException with an explanatory detail message.
- [style] Each route function is decorated with @router.<method>(path, summary=..., operation_id=...) and includes a docstring describing parameters, matching the FastAPI-MCP tool-description convention.
- [naming] Module-level private helper functions used only within a route file are prefixed with a single underscore (e.g. _find_epic_link_field, _resolve_version_names).
- [structure] Each source file starts with a module-level docstring summarizing its purpose, followed by stdlib imports, then third-party imports, then local imports.
- [testing] Tests are organized into pytest classes grouped by endpoint area (e.g. TestHealthEndpoints, TestPageEndpoints) using a shared 'client' fixture and mocked service clients (e.g. mock_confluence).
- [naming] Each module obtains its own logger via logger = logging.getLogger(__name__) immediately after imports.

## Workflows

| Command | Purpose | Verified |
| --- | --- | --- |
| `pip install -r requirements.txt` | Install root server dependencies | no |
| `pip install -r jira-mcp/requirements.txt` | Install jira-mcp dependencies | no |
| `pip install -r confluence-mcp/requirements.txt` | Install confluence-mcp dependencies | no |
| `cd jira-mcp && pytest` | Run jira-mcp tests | no |
| `cd confluence-mcp && pytest` | Run confluence-mcp tests | no |
| `uvicorn server:app --host 0.0.0.0 --port 8080` | Run root MCP server | no |
| `uvicorn mcp_server:app --host 0.0.0.0 --port 8000 --reload` | Run jira-mcp proxy server | no |
| `uvicorn mcp_server:app --host 0.0.0.0 --port 8001 --reload` | Run confluence-mcp proxy server | no |
| `docker-compose up -d` | Build and run all services with Docker Compose | no |
| `playwright install chromium` | Install Playwright browser for PDF export | no |
| `python server.py` | Start mlb-testplan MCP server | no |
| `docker-compose up -d` | Start jira-mcp server via Docker Compose | no |
| `./start-mcp.sh` | Start jira-mcp server locally (Linux/Mac) | no |
| `bash test_mcp_client.sh` | Run jira-mcp bash test client | no |
| `docker-compose up -d` | Start confluence-mcp server via Docker Compose | no |
| `./start-mcp.sh` | Start confluence-mcp server locally | no |
| `python test_client.py` | Run confluence-mcp interactive Python test client | no |
| `python simple_test.py` | Run confluence-mcp automated simple test | no |

## Invariants

- Each MCP subproject (root mlb-testplan-mcp, jira-mcp, confluence-mcp) is built as an independent FastAPI + fastapi_mcp application with its own entrypoint, requirements file, Dockerfile, and port, and can be run and deployed standalone.
- jira-mcp and confluence-mcp validate required credentials (JIRA_PAT / CONFLUENCE_PAT) at module import time in config.py by raising RuntimeError, so any code path that imports config (server startup, tests, tooling) fails immediately if the PAT env var is missing rather than failing lazily on first API call.
- In jira-mcp and confluence-mcp, every FastAPI route handler body is wrapped in try/except Exception and converted into an HTTPException with an explanatory detail message; no route lets a raw exception propagate to the client.
- All routers in jira-mcp and confluence-mcp are registered exclusively through a single routes/__init__.py::register_routes(app) function called from the service's mcp_server.py; there is no ad-hoc app.include_router() call elsewhere in the codebase.
- Shared xRay v2 API interaction logic (error handling, response passthrough, pagination, field extraction) is centralized in utils/xray helper functions rather than reimplemented in each route/report-building function of the root server.
- For MLB test-plan failure-analysis workflows, agents are constrained to use only the mlb-testplan MCP tools and are prohibited from invoking the separate Jira MCP, Confluence MCP, or GitLab MCP servers, keeping the three MCP services logically isolated at the agent-orchestration layer despite being co-located in one repository.

## Gotchas & Landmines

- jira-mcp and confluence-mcp raise RuntimeError at module import time if JIRA_PAT/CONFLUENCE_PAT env vars are unset, so simply importing config.py (e.g. in an unrelated test or tool) crashes before any server code runs.
- config.SPRINT_FIELD_ID is a mutable module-level global that discover_sprint_field() mutates as a cache; since it's shared process-wide, concurrent requests hitting different Jira instances (or test isolation) can read a stale/incorrect field ID unless explicitly reset.
- server.py's parallel fetch helpers (ThreadPoolExecutor + as_completed) swallow all per-task exceptions with bare `except Exception: continue` or default-value fallback, silently hiding network/auth failures as empty results rather than surfacing them.
- server.py hardcodes a default corporate proxy (http://http-proxy.porsche.org:3133) as a fallback for HTTP_PROXY, so requests silently route through that proxy in environments where it isn't reachable/relevant, instead of failing fast or defaulting to no proxy.
- confluence-mcp/config.py prints connection/proxy info via bare print() at import time instead of using the logging module, so these startup diagnostics bypass log level filtering and can leak into stdout of any process that imports config.

## Anti-Patterns

- Avoid: Avoid catching bare 'except Exception' broadly around large blocks of logic instead of catching specific exception types, which can mask unrelated errors.
- Avoid: Avoid embedding secrets/config defaults such as internal proxy URLs directly in source as fallback values for environment variables.

## Architectural Patterns

- Router-per-domain pattern: each MCP service (jira-mcp, confluence-mcp) splits its FastAPI endpoints into per-domain modules under routes/ (e.g. issues.py, pages.py), each exposing its own APIRouter, aggregated by a single register_routes(app) entrypoint.
- Multi-service monorepo architecture: three independently deployable FastAPI+fastapi_mcp servers (root xRay test-plan server, jira-mcp, confluence-mcp) live side-by-side in one repository, each with its own Dockerfile, composed together via a top-level docker-compose.yml.
- Shared-utility-module pattern: cross-cutting integration logic for an external API (xRay) is factored out into a dedicated utils/ package consumed by route/report code, rather than duplicated per endpoint.
- Test-class-per-endpoint-area pattern: pytest suites group related endpoint tests into classes (e.g. TestHealthEndpoints, TestPageEndpoints) sharing a common 'client' fixture and mocked external-service client, isolating tests from real Jira/Confluence calls.

## Verified Prior-Doc Facts

- The mlb-testplan MCP root server exposes an MCP tool interface started via `python server.py`, listening on http://localhost:8080 with docs at /docs and a dashboard at /dashboard.
- The confluence-mcp subproject connects to Confluence via a PAT, defaults to base URL https://api.skyway.porsche.com/confluence, and runs its own MCP server (default port 8001) supporting docker-compose or ./start-mcp.sh startup.
- confluence-mcp exposes REST-style endpoints (e.g. /create_page, /page/{page_id}, /search, /search_cql, /spaces) rather than only MCP tool calls, and documents them individually in its README.
