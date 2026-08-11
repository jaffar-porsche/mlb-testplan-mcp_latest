"""Route modules for Confluence MCP Server."""
from routes.pages import router as pages_router
from routes.search import router as search_router
from routes.hierarchy import router as hierarchy_router
from routes.comments import router as comments_router
from routes.health import router as health_router
from routes.users import router as users_router


def register_routes(app):
    """Register all route modules with the FastAPI app."""
    app.include_router(pages_router)
    app.include_router(search_router)
    app.include_router(hierarchy_router)
    app.include_router(comments_router)
    app.include_router(health_router)
    app.include_router(users_router)
