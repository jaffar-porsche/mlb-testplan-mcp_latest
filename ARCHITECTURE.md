# Architecture

## Overview

This repository is a **multi-service monorepo** containing three independently
deployable FastAPI + `fastapi_mcp` servers, each with its own Dockerfile, that
are composed together via a top-level `docker-compose.yml`:

- **`mlb-testplan-mcp` (root server, `server.py`)** — a FastAPI-based xRay
  test-plan MCP server that proxies to the xRay v2 API to build a FAIL test
  report with KPM IDs, handling both Test Plan and single Test issue types.
  It exposes an MCP tool interface started via `python server.py`, listening
  on `http://localhost:8080` with docs at `/docs` and a dashboard at
  `/dashboard`.
- **`jira-mcp`** — a Model Context Protocol server for Jira integration,
  providing issue management, hierarchy traversal, and sprint management.
- **`confluence-mcp`** — a Model Context Protocol server for Confluence
  integration, providing page management, search, hierarchy traversal, and
  comments. It connects to Confluence via a PAT, defaults to base URL
  `https://api.skyway.porsche.com/confluence`, and runs its own MCP server
  (default port 8001), supporting `docker-compose` or `./start-mcp.sh`
  startup. It exposes REST-style endpoints (e.g. `/create_page`,
  `/page/{page_id}`, `/search`, `/search_cql`, `/spaces`) rather than only
  MCP tool calls.

## Architectural Patterns

### Router-per-domain
Each MCP service (`jira-mcp`, `confluence-mcp`) splits its FastAPI endpoints
into per-domain modules under `routes/` (e.g. `issues.py`, `pages.py`), each
exposing its own `APIRouter`, aggregated by a single `register_routes(app)`
entrypoint (see `jira-mcp/routes/__init__.py`).

### Multi-service monorepo
Three independently deployable FastAPI+fastapi_mcp servers (root xRay
test-plan server, `jira-mcp`, `confluence-mcp`) live side-by-side in one
repository, each with its own Dockerfile, composed together via a top-level
`docker-compose.yml`.

### Shared-utility-module
Cross-cutting integration logic for the xRay API is factored out into a
dedicated `utils/` package consumed by route/report code, rather than
duplicated per endpoint. Shared xRay v2 API interaction logic (error
handling, response passthrough, pagination, field extraction) is centralized
in `utils/xray` helper functions rather than reimplemented in each
route/report-building function of the root server.

### Test-class-per-endpoint-area
Pytest suites group related endpoint tests into classes (e.g.
`TestHealthEndpoints`, `TestPageEndpoints`) sharing a common `client`
fixture and mocked external-service client, isolating tests from real
Jira/Confluence calls.

## Invariants

- Each MCP subproject (root `mlb-testplan-mcp`, `jira-mcp`, `confluence-mcp`)
  is built as an independent FastAPI + `fastapi_mcp` application with its
  own entrypoint, requirements file, Dockerfile, and port, and can be run and
  deployed standalone.
- `jira-mcp` and `confluence-mcp` validate required credentials
  (`JIRA_PAT` / `CONFLUENCE_PAT`) at module import time in `config.py` by
  raising `RuntimeError`, so any code path that imports `config` (server
  startup, tests, tooling) fails immediately if the PAT env var is missing
  rather than failing lazily on first API call.
- In `jira-mcp` and `confluence-mcp`, every FastAPI route handler body is
  wrapped in `try/except Exception` and converted into an `HTTPException`
  with an explanatory detail message; no route lets a raw exception
  propagate to the client.
- All routers in `jira-mcp` and `confluence-mcp` are registered exclusively
  through a single `routes/__init__.py::register_routes(app)` function
  called from the service's `mcp_server.py`; there is no ad-hoc
  `app.include_router()` call elsewhere in the codebase.
- For MLB test-plan failure-analysis workflows, agents are constrained to
  use only the mlb-testplan MCP tools and are prohibited from invoking the
  separate Jira MCP, Confluence MCP, or GitLab MCP servers, keeping the
  three MCP services logically isolated at the agent-orchestration layer
  despite being co-located in one repository.

## Entry Points

| Service | Entry point | Default port |
| --- | --- | --- |
| Root server | `server.py` | 8080 |
| jira-mcp | `jira-mcp/mcp_server.py` | 8000 |
| confluence-mcp | `confluence-mcp/mcp_server.py` | 8001 |
</content>
