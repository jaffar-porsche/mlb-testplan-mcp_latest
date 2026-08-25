# Gotchas

- jira-mcp and confluence-mcp raise RuntimeError at module import time if JIRA_PAT/CONFLUENCE_PAT env vars are unset, so simply importing config.py (e.g. in an unrelated test or tool) crashes before any server code runs.
- config.SPRINT_FIELD_ID is a mutable module-level global that discover_sprint_field() mutates as a cache; since it's shared process-wide, concurrent requests hitting different Jira instances (or test isolation) can read a stale/incorrect field ID unless explicitly reset.
- server.py's parallel fetch helpers (ThreadPoolExecutor + as_completed) swallow all per-task exceptions with bare `except Exception: continue` or default-value fallback, silently hiding network/auth failures as empty results rather than surfacing them.
- server.py hardcodes a default corporate proxy (http://http-proxy.porsche.org:3133) as a fallback for HTTP_PROXY, so requests silently route through that proxy in environments where it isn't reachable/relevant, instead of failing fast or defaulting to no proxy.
- confluence-mcp/config.py prints connection/proxy info via bare print() at import time instead of using the logging module, so these startup diagnostics bypass log level filtering and can leak into stdout of any process that imports config.
