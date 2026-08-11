"""Route modules for Jira MCP Server."""
from fastapi import APIRouter

from routes.issues import router as issues_router
from routes.attachments import router as attachments_router
from routes.comments import router as comments_router
from routes.projects import router as projects_router
from routes.sprints import router as sprints_router
from routes.links import router as links_router
from routes.remote_links import router as remote_links_router
from routes.teams import router as teams_router
from routes.users import router as users_router
from routes.servicedesk import router as servicedesk_router
from routes.xray import router as xray_router


def register_routes(app):
    """Register all route modules with the FastAPI app."""
    app.include_router(issues_router)
    app.include_router(attachments_router)
    app.include_router(comments_router)
    app.include_router(projects_router)
    app.include_router(sprints_router)
    app.include_router(links_router)
    app.include_router(remote_links_router)
    app.include_router(teams_router)
    app.include_router(users_router)
    app.include_router(servicedesk_router)
    app.include_router(xray_router)
