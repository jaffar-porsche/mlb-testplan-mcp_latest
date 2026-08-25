# Architectural Patterns

- Router-per-domain pattern: each MCP service (jira-mcp, confluence-mcp) splits its FastAPI endpoints into per-domain modules under routes/ (e.g. issues.py, pages.py), each exposing its own APIRouter, aggregated by a single register_routes(app) entrypoint.
- Multi-service monorepo architecture: three independently deployable FastAPI+fastapi_mcp servers (root xRay test-plan server, jira-mcp, confluence-mcp) live side-by-side in one repository, each with its own Dockerfile, composed together via a top-level docker-compose.yml.
- Shared-utility-module pattern: cross-cutting integration logic for an external API (xRay) is factored out into a dedicated utils/ package consumed by route/report code, rather than duplicated per endpoint.
- Test-class-per-endpoint-area pattern: pytest suites group related endpoint tests into classes (e.g. TestHealthEndpoints, TestPageEndpoints) sharing a common 'client' fixture and mocked external-service client, isolating tests from real Jira/Confluence calls.
