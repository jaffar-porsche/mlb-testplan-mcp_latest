# Modules

## `mlb-testplan-mcp` (root server)
- **Path:** `.`
- **Purpose:** A FastAPI-based xRay test-plan MCP server that proxies to the
  xRay v2 API to build a FAIL test report with KPM IDs, handling both Test
  Plan and single Test issue types. Started via `python server.py`, listening
  on `http://localhost:8080` with docs at `/docs` and a dashboard at
  `/dashboard`.
- **External deps:** `fastapi`, `fastapi_mcp`, `httpx`, `dotenv`, `bs4`,
  `pandas`.

## `jira-mcp`
- **Path:** `jira-mcp`
- **Purpose:** Entry point for a Jira MCP server (FastAPI + FastApiMCP) that
  registers route modules for issue management, hierarchy traversal, and
  sprint operations.
- **Public API:** `app`
- **External deps:** `fastapi`, `fastapi_mcp`

### `jira-mcp/routes`
- **Purpose:** Defines FastAPI routes for Jira issue CRUD, search, hierarchy
  and roadmap endpoints, built on top of the jira client and hierarchy
  utilities.
- **Public API:** `create_issue`, `get_issue`, `update_issue`,
  `search_issues`, `get_issue_hierarchy`, `get_issue_roadmap`
- **External deps:** `fastapi`

### `jira-mcp/utils`
- **Purpose:** Provides utility functions to recursively traverse Jira
  Epic/Feature/Story issue hierarchies and build markdown hierarchy trees
  and PI-based roadmaps.
- **Public API:** `HierarchyStats`, `get_issue_links`, `is_closed_status`,
  `get_child_issues`, `build_hierarchy_markdown`,
  `get_feature_with_versions`, `build_roadmap_markdown`

### `jira-mcp/tests`
- **Purpose:** Pytest test suite verifying that all Jira MCP route modules
  import correctly and expose their expected endpoint paths.
- **Public API:** `test_routes_module_imports`,
  `test_issues_router_has_routes`
- **External deps:** `pytest`

## `confluence-mcp`
- **Path:** `confluence-mcp`
- **Purpose:** Entry point for a Confluence MCP server (FastAPI +
  FastApiMCP) that registers route modules for page management, search,
  hierarchy traversal, and comments. Connects to Confluence via a PAT,
  defaults to base URL `https://api.skyway.porsche.com/confluence`, and runs
  on default port 8001, supporting `docker-compose` or `./start-mcp.sh`
  startup.
- **Public API:** `app`
- **External deps:** `fastapi`, `fastapi_mcp`

### `confluence-mcp/routes`
- **Purpose:** Implements Confluence page CRUD endpoints (create, get,
  update, move, delete, including cascading delete of descendant pages) via
  the confluence client. Exposes REST-style endpoints (e.g. `/create_page`,
  `/page/{page_id}`, `/search`, `/search_cql`, `/spaces`) rather than only
  MCP tool calls.
- **Public API:** `create_page`, `create_page_simple`, `get_page`,
  `update_page`, `move_page`, `delete_page`
- **External deps:** `fastapi`

### `confluence-mcp/integration`
- **Purpose:** Provides client integration templates and configs (Claude
  Desktop config, VS Code/Copilot prompts, Postman collection, HTTP request
  files) for connecting external MCP clients to the Confluence MCP server.

### `confluence-mcp/tests`
- **Purpose:** Pytest test suite covering Confluence MCP endpoints,
  including health checks, using mocked Confluence client responses.
- **Public API:** `TestHealthEndpoints`
- **External deps:** `pytest`

## `utils`
- **Path:** `utils`
- **Purpose:** Shared helper functions for proxying and interpreting xRay v2
  API responses (error handling, response passthrough, test
  run/plan/exec retrieval, and payload field extraction) used across MCP
  routes.
- **Public API:** `raise_for_xray`, `proxy_response`, `request_xray`,
  `get_xray`, `get_testruns`, `get_testplan_tests`, `get_testexec_tests`,
  `build_step_fields`, `extract_items`, `get_jira_issue_metadata`
- **External deps:** `fastapi`
</content>
