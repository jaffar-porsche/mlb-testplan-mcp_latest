"""User search operations for Confluence."""
import logging

from fastapi import APIRouter, HTTPException, Query

from client import confluence

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Users"])


def _sanitize_cql_value(value: str) -> str:
    """Escape double quotes in a CQL string value."""
    return value.replace('"', '\\"')


def _format_user(user: dict) -> dict:
    """Extract a consistent dict from a Confluence user result."""
    return {
        "username": user.get("username") or user.get("userKey"),
        "displayName": user.get("displayName"),
        "userKey": user.get("userKey"),
        "type": user.get("type", "known"),
    }


@router.get(
    "/users/search",
    summary="Search Confluence users",
    operation_id="search_users",
)
async def search_users(
    query: str = Query(description="Name or username to search for"),
    max_results: int = Query(default=10, le=50),
):
    """
    Search for Confluence users by display name or username.

    Uses CQL user search via the standard search endpoint with
    `type = "user" AND user.fullname ~ "query"`.

    Falls back to exact username lookup if CQL search is unavailable
    (e.g. on older Confluence versions).

    Parameters:
    - query: Search string (matches display name or username)
    - max_results: Maximum number of results (default 10, max 50)
    """
    try:
        safe_query = _sanitize_cql_value(query)
        cql = f'type = "user" AND user.fullname ~ "{safe_query}"'

        response = confluence._session.get(
            f"{confluence.url}/rest/api/search",
            params={"cql": cql, "limit": max_results},
        )

        if response.status_code != 200:
            logger.warning(
                "CQL user search returned %d, falling back to username lookup",
                response.status_code,
            )
            return _fallback_username_lookup(query)

        data = response.json()
        results = data.get("results", [])
        users = []
        for result in results:
            user_data = result.get("user", result)
            users.append(_format_user(user_data))

        return {
            "total": len(users),
            "users": users,
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to search users: {e}"
        )


def _fallback_username_lookup(query: str) -> dict:
    """Exact username lookup as fallback when CQL search is unavailable."""
    try:
        user = confluence.get_user_details_by_username(query)
        if user:
            return {"total": 1, "users": [_format_user(user)]}
    except Exception:
        pass
    return {"total": 0, "users": []}
