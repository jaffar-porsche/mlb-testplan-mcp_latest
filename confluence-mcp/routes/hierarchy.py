"""Page hierarchy traversal operations for Confluence."""
import logging

from fastapi import APIRouter, HTTPException

from client import confluence
from config import CONFLUENCE_BASE_URL

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Hierarchy"])


@router.get("/page/{page_id}/children", summary="Get child pages of a Confluence page", operation_id="get_child_pages")
async def get_child_pages(page_id: str, start: int = 0, limit: int = 50, fetch_all: str = "false"):
    """
    Retrieve direct child pages of a specific Confluence page.
    Useful for traversing page hierarchies.

    Parameters:
    - page_id: The parent page ID
    - start: Pagination offset (default 0)
    - limit: Max results per request (default 50, max 200)
    - fetch_all: If "true", fetches ALL children regardless of limit (use with caution on large trees)
    """
    try:
        fetch_all = str(fetch_all).lower() in ("true", "1", "yes")
        limit = min(limit, 200)

        if fetch_all:
            children, total = _fetch_all_children(page_id)
        else:
            children, total, has_more = _fetch_children_page(page_id, start, limit)
            return {
                "parent_id": page_id,
                "children": children,
                "total": total,
                "start": start,
                "limit": limit,
                "has_more": has_more
            }

        return {
            "parent_id": page_id,
            "children": children,
            "total": total,
            "start": 0,
            "limit": total,
            "has_more": False
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get child pages: {e}")


def _fetch_children_page(page_id: str, start: int, limit: int):
    """Fetch a single page of children with accurate total and has_more."""
    response = confluence._session.get(
        f"{confluence.url}/rest/api/content/{page_id}/child/page",
        params={"start": start, "limit": limit, "expand": "space,version"}
    )

    if response.status_code != 200:
        raise Exception(f"API returned {response.status_code}: {response.text}")

    data = response.json()
    total = data.get("size", 0)
    children = _parse_children(data.get("results", []))

    # Confluence size field is unreliable for total count — check _links for next
    has_more = "next" in data.get("_links", {})

    return children, total, has_more


def _fetch_all_children(page_id: str):
    """Fetch all children using pagination."""
    all_children = []
    batch_start = 0
    batch_size = 200

    while True:
        response = confluence._session.get(
            f"{confluence.url}/rest/api/content/{page_id}/child/page",
            params={"start": batch_start, "limit": batch_size, "expand": "space,version"}
        )

        if response.status_code != 200:
            raise Exception(f"API returned {response.status_code}: {response.text}")

        data = response.json()
        results = data.get("results", [])
        all_children.extend(_parse_children(results))

        if "next" not in data.get("_links", {}):
            break
        batch_start += batch_size

    return all_children, len(all_children)


def _parse_children(results: list) -> list:
    """Parse child page results into response format."""
    return [
        {
            "id": child["id"],
            "title": child["title"],
            "space": child.get("space", {}).get("key", ""),
            "version": child.get("version", {}).get("number", 0),
            "url": f"{CONFLUENCE_BASE_URL}/pages/viewpage.action?pageId={child['id']}"
        }
        for child in results
    ]


@router.get("/page/{page_id}/ancestors", summary="Get ancestor pages of a Confluence page", operation_id="get_page_ancestors")
async def get_page_ancestors(page_id: str):
    """
    Retrieve the ancestor (parent) chain of a specific Confluence page.
    Returns pages from root to immediate parent.
    """
    try:
        page = confluence.get_page_by_id(
            page_id,
            expand="ancestors,space"
        )

        ancestors = []
        for ancestor in page.get("ancestors", []):
            ancestors.append({
                "id": ancestor["id"],
                "title": ancestor["title"],
                "url": f"{CONFLUENCE_BASE_URL}/pages/viewpage.action?pageId={ancestor['id']}"
            })

        return {
            "page_id": page_id,
            "page_title": page.get("title", ""),
            "space": page.get("space", {}).get("key", ""),
            "ancestors": ancestors,
            "depth": len(ancestors)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get page ancestors: {e}")
