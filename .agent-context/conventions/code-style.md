# Conventions

- Each MCP service (jira-mcp, confluence-mcp) organizes FastAPI endpoints into per-domain modules under a routes/ package, with a routes/__init__.py exposing a register_routes(app) function that includes each router.
- Route handler bodies wrap their logic in try/except Exception blocks and convert failures into fastapi.HTTPException with an explanatory detail message.
- Each route function is decorated with @router.<method>(path, summary=..., operation_id=...) and includes a docstring describing parameters, matching the FastAPI-MCP tool-description convention.
- Module-level private helper functions used only within a route file are prefixed with a single underscore (e.g. _find_epic_link_field, _resolve_version_names).
- Each source file starts with a module-level docstring summarizing its purpose, followed by stdlib imports, then third-party imports, then local imports.
- Tests are organized into pytest classes grouped by endpoint area (e.g. TestHealthEndpoints, TestPageEndpoints) using a shared 'client' fixture and mocked service clients (e.g. mock_confluence).
- Each module obtains its own logger via logger = logging.getLogger(__name__) immediately after imports.
