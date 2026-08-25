# Conventions

## Structure

- Each MCP service (`jira-mcp`, `confluence-mcp`) organizes FastAPI endpoints
  into per-domain modules under a `routes/` package, with a
  `routes/__init__.py` exposing a `register_routes(app)` function that
  includes each router.
- Each source file starts with a module-level docstring summarizing its
  purpose, followed by stdlib imports, then third-party imports, then local
  imports.

## Style

- Route handler bodies wrap their logic in `try/except Exception` blocks and
  convert failures into `fastapi.HTTPException` with an explanatory detail
  message.
- Each route function is decorated with
  `@router.<method>(path, summary=..., operation_id=...)` and includes a
  docstring describing parameters, matching the FastAPI-MCP tool-description
  convention.

## Naming

- Module-level private helper functions used only within a route file are
  prefixed with a single underscore (e.g. `_find_epic_link_field`,
  `_resolve_version_names`).
- Each module obtains its own logger via
  `logger = logging.getLogger(__name__)` immediately after imports.

## Testing

- Tests are organized into pytest classes grouped by endpoint area (e.g.
  `TestHealthEndpoints`, `TestPageEndpoints`) using a shared `client` fixture
  and mocked service clients (e.g. `mock_confluence`).
- `jira-mcp` and `confluence-mcp` each define their own `pytest.ini` with
  `testpaths = tests`, `python_files = test_*.py`, `python_classes = Test*`,
  `python_functions = test_*`.
- Run tests per subproject: `cd jira-mcp && pytest` or
  `cd confluence-mcp && pytest`.

## Anti-Patterns

- Avoid catching bare `except Exception` broadly around large blocks of
  logic instead of catching specific exception types, which can mask
  unrelated errors.
- Avoid embedding secrets/config defaults such as internal proxy URLs
  directly in source as fallback values for environment variables (e.g.
  `server.py` hardcodes a default corporate proxy,
  `http://http-proxy.porsche.org:3133`, as a fallback for `HTTP_PROXY`).

## Known Gotchas

- `jira-mcp` and `confluence-mcp` raise `RuntimeError` at module import time
  if `JIRA_PAT`/`CONFLUENCE_PAT` env vars are unset, so simply importing
  `config.py` (e.g. in an unrelated test or tool) crashes before any server
  code runs.
- `config.SPRINT_FIELD_ID` is a mutable module-level global that
  `discover_sprint_field()` mutates as a cache; since it's shared
  process-wide, concurrent requests hitting different Jira instances (or
  test isolation) can read a stale/incorrect field ID unless explicitly
  reset.
- `server.py`'s parallel fetch helpers (`ThreadPoolExecutor` + `as_completed`)
  swallow all per-task exceptions with a bare `except Exception: continue` or
  default-value fallback, silently hiding network/auth failures as empty
  results rather than surfacing them.
- `confluence-mcp/config.py` prints connection/proxy info via bare `print()`
  at import time instead of using the logging module, so these startup
  diagnostics bypass log level filtering and can leak into stdout of any
  process that imports `config`.

## Setup & Workflows

- Install root server dependencies: `pip install -r requirements.txt`
- Install `jira-mcp` dependencies: `pip install -r jira-mcp/requirements.txt`
- Install `confluence-mcp` dependencies:
  `pip install -r confluence-mcp/requirements.txt`
- Install Playwright browser for PDF export: `playwright install chromium`
- Run root MCP server: `uvicorn server:app --host 0.0.0.0 --port 8080`
- Run `jira-mcp` proxy server:
  `uvicorn mcp_server:app --host 0.0.0.0 --port 8000 --reload`
- Run `confluence-mcp` proxy server:
  `uvicorn mcp_server:app --host 0.0.0.0 --port 8001 --reload`
- Build and run all services together: `docker-compose up -d`
</content>
