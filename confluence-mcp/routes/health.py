"""Health check and connection test endpoints."""
import logging

from fastapi import APIRouter

from client import confluence
from config import CONFLUENCE_BASE_URL

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Health"])


@router.get("/health", summary="Health check endpoint", operation_id="health_check")
async def health_check():
    """
    Simple health check to verify server is running.
    """
    return {
        "status": "healthy",
        "service": "Confluence MCP Server",
        "version": "2.0.0"
    }


@router.get("/test_connection", summary="Test Confluence connection and authentication", operation_id="test_connection")
async def test_connection():
    """
    Test the Confluence connection and authentication.
    """
    try:
        user_info = confluence.get_current_user()
        return {
            "status": "connected",
            "user": user_info.get("displayName", user_info.get("username", "Unknown")),
            "base_url": CONFLUENCE_BASE_URL,
            "message": "Authentication successful"
        }
    except Exception as e:
        try:
            spaces = confluence.get_all_spaces(start=0, limit=1)
            return {
                "status": "connected",
                "user": "API User",
                "base_url": CONFLUENCE_BASE_URL,
                "message": "Authentication successful (verified via spaces API)",
                "spaces_available": len(spaces.get("results", []))
            }
        except Exception as fallback_error:
            return {
                "status": "failed",
                "error": str(e),
                "fallback_error": str(fallback_error),
                "base_url": CONFLUENCE_BASE_URL,
                "message": "Authentication or connectivity failed"
            }
