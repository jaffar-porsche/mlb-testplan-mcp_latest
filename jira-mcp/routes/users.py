"""User search operations."""
import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from client import jira

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Users"])


def _format_user(user) -> dict:
    """Extract a consistent dict from a jira User object."""
    return {
        "username": getattr(user, "name", None) or getattr(user, "key", None),
        "displayName": getattr(user, "displayName", None),
        "emailAddress": getattr(user, "emailAddress", None),
        "active": getattr(user, "active", None),
    }


@router.get(
    "/users/search",
    summary="Search Jira users",
    operation_id="search_users",
)
async def search_users(
    query: str = Query(description="Name, username, or email to search for"),
    project_key: Optional[str] = Query(
        default=None,
        description="If provided, only return users assignable to this project",
    ),
    max_results: int = Query(default=10, le=50),
):
    """
    Search for Jira users by name, username, or email.

    When project_key is provided, results are limited to users who can be
    assigned issues in that project (respects project permissions).

    Parameters:
    - query: Search string (matches display name, username, or email)
    - project_key: Optional project key to filter by assignable users
    - max_results: Maximum number of results (default 10, max 50)
    """
    try:
        if project_key:
            users = jira.search_assignable_users_for_issues(
                username=query,
                project=project_key,
                maxResults=max_results,
            )
        else:
            users = jira.search_users(
                user=query,
                maxResults=max_results,
            )

        return {
            "total": len(users),
            "users": [_format_user(u) for u in users],
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to search users: {e}")
