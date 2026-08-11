"""Search and space operations for Confluence."""
import logging

from fastapi import APIRouter, HTTPException

from client import confluence
from config import CONFLUENCE_BASE_URL

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Search"])


@router.get("/search", summary="Search Confluence content by text", operation_id="search_content")
async def search_content(
    query: str,
    limit: int = 10,
    space_key: str = None
):
    """
    Full-text search across Confluence page content.

    Searches for a term or phrase within page bodies and titles,
    similar to typing into the Confluence search bar.

    Parameters:
    - query: The text to search for (e.g. "KD-VBV", "Angular cache")
    - space_key: Optional space key to restrict search to a single space
    - limit: Max results to return (default 10)
    """
    try:
        if space_key:
            cql_query = f"space = '{space_key}' AND text ~ '{query}'"
        else:
            cql_query = f"text ~ '{query}'"

        return _execute_cql(cql_query, limit)
    except Exception as e:
        error_detail = f"Text search failed: {str(e)}. Try using /search_simple with a space_key instead."
        raise HTTPException(status_code=500, detail=error_detail)


@router.get("/search_cql", summary="Search Confluence with raw CQL", operation_id="search_cql")
async def search_cql(
    cql: str,
    limit: int = 25
):
    """
    Execute a raw CQL (Confluence Query Language) query.

    Use this for structural queries that go beyond simple text search,
    such as filtering by page type, ancestor, label, or creation date.

    Parameters:
    - cql: The CQL query (e.g. "type = page AND space = PCDS AND ancestor = 27075880")
    - limit: Max results to return (default 25)

    Common CQL examples:
    - All pages in a space: "type = page AND space = TEST"
    - Pages under a parent: "type = page AND ancestor = 12345"
    - Pages by label: "type = page AND label = 'architecture'"
    - Recently modified: "type = page AND space = TEST AND lastModified > now('-7d')"
    """
    try:
        return _execute_cql(cql, limit)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"CQL query failed: {str(e)}")


def _execute_cql(cql_query: str, limit: int) -> dict:
    """Execute a CQL query and return formatted results."""
    results = confluence.cql(cql_query, limit=limit)

    search_results = []
    if results and "results" in results:
        for result in results["results"]:
            content = result.get("content") or result

            search_result = {
                "id": content.get("id", ""),
                "title": content.get("title", ""),
                "type": content.get("type", ""),
                "space": None,
                "url": ""
            }

            if "space" in content and content["space"]:
                search_result["space"] = content["space"].get("key", "")

            if search_result["id"]:
                search_result["url"] = f"{CONFLUENCE_BASE_URL}/pages/viewpage.action?pageId={search_result['id']}"

            search_results.append(search_result)

    return {
        "results": search_results,
        "total": results.get("size", len(search_results))
    }


@router.get("/search_simple", summary="Simple search in specific space", operation_id="search_simple")
async def search_simple(
    space_key: str,
    query: str = "",
    start: int = 0,
    limit: int = 50
):
    """
    Simple search within a specific space. Paginates through all pages
    to find matches by title (case-insensitive substring match).

    Parameters:
    - space_key: The Confluence space key
    - query: Optional title filter (case-insensitive substring). Omit to list all pages.
    - start: Pagination offset for results (default 0)
    - limit: Max results to return (default 50, max 200)
    """
    try:
        limit = min(limit, 200)
        all_pages = _fetch_all_space_pages(space_key)

        filtered_pages = []
        for page in all_pages:
            if not query or query.lower() in page.get("title", "").lower():
                filtered_pages.append({
                    "id": page["id"],
                    "title": page["title"],
                    "type": "page",
                    "space": space_key,
                    "url": f"{CONFLUENCE_BASE_URL}/pages/viewpage.action?pageId={page['id']}"
                })

        paginated = filtered_pages[start:start + limit]

        return {
            "results": paginated,
            "total": len(filtered_pages),
            "start": start,
            "limit": limit,
            "has_more": (start + limit) < len(filtered_pages)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to search in space: {e}")


@router.get(
    "/space/{space_key}/pages",
    summary="List all pages in a space with parent info",
    operation_id="list_space_pages"
)
async def list_space_pages(
    space_key: str,
    start: int = 0,
    limit: int = 100
):
    """
    List all pages in a Confluence space, including each page's parent ID.
    Useful for discovering orphan pages and understanding the full page tree.

    Parameters:
    - space_key: The Confluence space key
    - start: Pagination offset (default 0)
    - limit: Max results per request (default 100, max 200)
    """
    try:
        limit = min(limit, 200)

        all_pages = _fetch_all_space_pages(space_key, expand="ancestors")

        page_list = []
        for page in all_pages:
            ancestors = page.get("ancestors", [])
            parent_id = ancestors[-1]["id"] if ancestors else None

            page_list.append({
                "id": page["id"],
                "title": page["title"],
                "parent_id": parent_id,
                "space": space_key,
                "url": f"{CONFLUENCE_BASE_URL}/pages/viewpage.action?pageId={page['id']}"
            })

        paginated = page_list[start:start + limit]

        return {
            "pages": paginated,
            "total": len(page_list),
            "start": start,
            "limit": limit,
            "has_more": (start + limit) < len(page_list)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list pages in space: {e}")


def _fetch_all_space_pages(space_key: str, expand: str = None) -> list:
    """Fetch all pages in a space using pagination."""
    all_pages = []
    batch_start = 0
    batch_size = 200

    while True:
        params = {
            "spaceKey": space_key,
            "type": "page",
            "start": batch_start,
            "limit": batch_size,
        }
        if expand:
            params["expand"] = expand

        response = confluence._session.get(
            f"{confluence.url}/rest/api/content",
            params=params
        )

        if response.status_code != 200:
            raise Exception(f"API returned {response.status_code}: {response.text}")

        data = response.json()
        results = data.get("results", [])
        all_pages.extend(results)

        if len(results) < batch_size:
            break
        batch_start += batch_size

    return all_pages


@router.get("/spaces", summary="List available spaces", operation_id="list_spaces")
async def list_spaces():
    """
    List all available Confluence spaces.
    """
    try:
        spaces = confluence.get_all_spaces(start=0, limit=50)
        return {
            "spaces": [
                {
                    "key": space["key"],
                    "name": space["name"],
                    "type": space["type"],
                    "url": f"{CONFLUENCE_BASE_URL}/display/{space['key']}"
                }
                for space in spaces["results"]
            ],
            "total": spaces["size"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list spaces: {e}")
