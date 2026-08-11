"""Page CRUD operations for Confluence."""
import logging

from fastapi import APIRouter, HTTPException

from client import confluence
from config import CONFLUENCE_BASE_URL
from models import CreatePageRequest, UpdatePageRequest, MovePageRequest
from html_utils import sanitize_html_for_confluence

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Pages"])


@router.post("/create_page", summary="Create a new Confluence page", operation_id="create_page")
async def create_page(request: CreatePageRequest):
    """
    Create a new Confluence page.
    """
    try:
        try:
            space = confluence.get_space(request.space_key)
            logger.debug(f"Space '{request.space_key}' found: {space.get('name', 'Unknown')}")
        except Exception as space_error:
            logger.debug(f"Warning - could not verify space '{request.space_key}': {space_error}")

        sanitized_body = sanitize_html_for_confluence(request.body)

        if request.parent_id:
            page_data = {
                "type": "page",
                "title": request.title,
                "space": {"key": request.space_key},
                "ancestors": [{"id": request.parent_id}],
                "body": {
                    "storage": {
                        "value": sanitized_body,
                        "representation": "storage"
                    }
                }
            }

            response = confluence._session.post(
                f"{confluence.url}/rest/api/content",
                json=page_data,
                headers={"Content-Type": "application/json"}
            )

            if response.status_code in (200, 201):
                new_page = response.json()
            else:
                raise ValueError(f"API returned {response.status_code}: {response.text}")
        else:
            try:
                new_page = confluence.create_page(
                    space=request.space_key,
                    title=request.title,
                    body=sanitized_body,
                    type='page',
                    representation='storage'
                )
            except Exception:
                page_data = {
                    "type": "page",
                    "title": request.title,
                    "space": {"key": request.space_key},
                    "body": {
                        "storage": {
                            "value": sanitized_body,
                            "representation": "storage"
                        }
                    }
                }

                response = confluence._session.post(
                    f"{confluence.url}/rest/api/content",
                    json=page_data,
                    headers={"Content-Type": "application/json"}
                )

                if response.status_code in (200, 201):
                    new_page = response.json()
                else:
                    raise ValueError(f"API returned {response.status_code}: {response.text}")

        return {
            "id": new_page["id"],
            "title": new_page["title"],
            "url": f"{CONFLUENCE_BASE_URL}/pages/viewpage.action?pageId={new_page['id']}",
            "space": new_page["space"]["key"]
        }
    except Exception as e:
        error_detail = f"Failed to create page in space '{request.space_key}': {str(e)}"
        raise HTTPException(status_code=500, detail=error_detail)


@router.post("/create_page_simple", summary="Create a page using simplified API call", operation_id="create_page_simple")
async def create_page_simple(request: CreatePageRequest):
    """
    Create a new Confluence page using a simplified approach.
    """
    try:
        sanitized_body = sanitize_html_for_confluence(request.body)

        if request.parent_id:
            page_data = {
                "type": "page",
                "title": request.title,
                "space": {"key": request.space_key},
                "ancestors": [{"id": request.parent_id}],
                "body": {
                    "storage": {
                        "value": sanitized_body,
                        "representation": "storage"
                    }
                }
            }

            response = confluence._session.post(
                f"{confluence.url}/rest/api/content",
                json=page_data,
                headers={"Content-Type": "application/json"}
            )

            if response.status_code in (200, 201):
                new_page = response.json()
            else:
                raise ValueError(f"API returned {response.status_code}: {response.text}")
        else:
            new_page = confluence.create_page(
                space=request.space_key,
                title=request.title,
                body=sanitized_body
            )

        return {
            "id": new_page.get("id", "unknown"),
            "title": new_page.get("title", request.title),
            "url": f"{CONFLUENCE_BASE_URL}/pages/viewpage.action?pageId={new_page.get('id', '')}",
            "space": request.space_key,
            "method": "simplified"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Simple create failed: {e}")


@router.get("/page/{page_id}", summary="Get Confluence page details", operation_id="get_page")
async def get_page(page_id: str):
    """
    Retrieve details for a specific Confluence page.
    """
    try:
        page = confluence.get_page_by_id(
            page_id,
            expand="body.storage,space,version"
        )
        return {
            "id": page["id"],
            "title": page["title"],
            "space": page["space"]["key"],
            "version": page["version"]["number"],
            "body": page["body"]["storage"]["value"],
            "url": f"{CONFLUENCE_BASE_URL}/pages/viewpage.action?pageId={page['id']}"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch page: {e}")


@router.put("/page/{page_id}", summary="Update a Confluence page", operation_id="update_page")
async def update_page(page_id: str, request: UpdatePageRequest):
    """
    Update an existing Confluence page.
    """
    try:
        current_page = confluence.get_page_by_id(
            page_id,
            expand="body.storage,space,version"
        )

        new_title = request.title if request.title else current_page["title"]
        new_body = request.body if request.body else current_page["body"]["storage"]["value"]
        new_body = sanitize_html_for_confluence(new_body)

        update_data = {
            "id": page_id,
            "type": "page",
            "title": new_title,
            "space": {"key": current_page["space"]["key"]},
            "version": {"number": current_page["version"]["number"] + 1},
            "body": {
                "storage": {
                    "value": new_body,
                    "representation": "storage"
                }
            }
        }

        response = confluence._session.put(
            f"{confluence.url}/rest/api/content/{page_id}",
            json=update_data,
            headers={"Content-Type": "application/json"}
        )

        if response.status_code == 200:
            updated_page = response.json()
            return {
                "id": updated_page["id"],
                "title": updated_page["title"],
                "url": f"{CONFLUENCE_BASE_URL}/pages/viewpage.action?pageId={updated_page['id']}",
                "version": updated_page["version"]["number"]
            }
        else:
            raise Exception(f"Update API returned {response.status_code}: {response.text}")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update page: {e}")


@router.put("/page/{page_id}/move", summary="Move a page to a new parent", operation_id="move_page")
async def move_page(page_id: str, request: MovePageRequest):
    """
    Move a Confluence page under a new parent, or to the space root.

    Reparents the page by updating its ancestors. All child pages move with it.

    Parameters:
    - page_id: The page to move
    - parent_id: Target parent page ID (omit or null to move to space root)
    """
    try:
        current_page = confluence.get_page_by_id(
            page_id,
            expand="body.storage,space,version,ancestors"
        )

        current_ancestors = [a["id"] for a in current_page.get("ancestors", [])]
        current_parent = current_ancestors[-1] if current_ancestors else None

        target_parent = request.parent_id
        if target_parent == current_parent:
            return {
                "id": page_id,
                "title": current_page["title"],
                "message": "Page is already under this parent — no move needed",
                "parent_id": target_parent or "root",
                "url": f"{CONFLUENCE_BASE_URL}/pages/viewpage.action?pageId={page_id}"
            }

        if target_parent:
            try:
                parent_page = confluence.get_page_by_id(
                    target_parent,
                    expand="ancestors"
                )
            except Exception:
                raise ValueError(f"Target parent page {target_parent} not found")

            parent_ancestor_ids = [a["id"] for a in parent_page.get("ancestors", [])]
            if page_id in parent_ancestor_ids or target_parent == page_id:
                raise ValueError(
                    f"Cannot move page {page_id} under {target_parent} — "
                    "target is the same page or a descendant of it"
                )

        ancestors = [{"id": target_parent}] if target_parent else []

        move_data = {
            "id": page_id,
            "type": "page",
            "title": current_page["title"],
            "space": {"key": current_page["space"]["key"]},
            "version": {"number": current_page["version"]["number"] + 1},
            "ancestors": ancestors,
            "body": {
                "storage": {
                    "value": current_page["body"]["storage"]["value"],
                    "representation": "storage"
                }
            }
        }

        response = confluence._session.put(
            f"{confluence.url}/rest/api/content/{page_id}",
            json=move_data,
            headers={"Content-Type": "application/json"}
        )

        if response.status_code == 200:
            moved_page = response.json()
            return {
                "id": moved_page["id"],
                "title": moved_page["title"],
                "parent_id": target_parent or "root",
                "previous_parent_id": current_parent or "root",
                "version": moved_page["version"]["number"],
                "url": f"{CONFLUENCE_BASE_URL}/pages/viewpage.action?pageId={moved_page['id']}"
            }
        else:
            raise Exception(f"Move API returned {response.status_code}: {response.text}")

    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to move page: {e}")


@router.delete("/page/{page_id}", summary="Delete a Confluence page", operation_id="delete_page")
async def delete_page(page_id: str, cascade: str = "false"):
    """
    Delete a Confluence page by ID.

    Parameters:
    - page_id: The page ID to delete (e.g., "2347613274")
    - cascade: If "false" (default), child pages are reparented to the deleted page's parent.
               If "true", the page and ALL descendant pages are deleted recursively.

    **Warning:** When cascade=false, any child pages will be reparented to the space root,
    which can create orphan pages. The response includes a `reparented_children` field
    listing any pages that were reparented. Consider using cascade=true when deleting
    pages that have children you also want removed.

    Pages are moved to trash and can be restored from the Confluence UI.
    """
    try:
        cascade = str(cascade).lower() in ("true", "1", "yes")

        # Fetch page details before deletion for confirmation response
        page = confluence.get_page_by_id(page_id, expand="space,version")
        page_title = page["title"]
        space_key = page["space"]["key"]

        # Check for direct children before deletion
        direct_children = _get_direct_children(page_id)

        deleted_pages = [{"id": page_id, "title": page_title}]

        if cascade:
            # Collect all descendant pages depth-first, delete bottom-up
            descendants = _collect_descendants(page_id)
            for desc in reversed(descendants):
                resp = confluence._session.delete(
                    f"{confluence.url}/rest/api/content/{desc['id']}"
                )
                if resp.status_code != 204:
                    raise Exception(
                        f"Failed to delete child page '{desc['title']}' ({desc['id']}): "
                        f"API returned {resp.status_code}: {resp.text}"
                    )
            deleted_pages.extend(descendants)

        # Delete the root page
        response = confluence._session.delete(
            f"{confluence.url}/rest/api/content/{page_id}"
        )

        if response.status_code == 204:
            result = {
                "success": True,
                "message": f"Page '{page_title}' deleted from space {space_key}"
                           + (f" (cascade: {len(deleted_pages)} pages total)" if cascade else ""),
                "id": page_id,
                "title": page_title,
                "space": space_key,
                "cascade": cascade,
                "deleted_count": len(deleted_pages),
                "deleted_pages": deleted_pages
            }

            # Warn about reparented children when not cascading
            if not cascade and direct_children:
                result["warning"] = (
                    f"{len(direct_children)} child page(s) were reparented to the space root. "
                    "Use cascade=true to delete children along with the parent."
                )
                result["reparented_children"] = direct_children

            return result
        else:
            raise Exception(f"Delete API returned {response.status_code}: {response.text}")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete page {page_id}: {e}")


def _get_direct_children(page_id: str) -> list:
    """Fetch direct children of a page (lightweight, no recursion)."""
    try:
        response = confluence._session.get(
            f"{confluence.url}/rest/api/content/{page_id}/child/page",
            params={"limit": 200}
        )
        if response.status_code != 200:
            return []
        return [
            {"id": child["id"], "title": child["title"]}
            for child in response.json().get("results", [])
        ]
    except Exception:
        return []


def _collect_descendants(page_id: str) -> list:
    """Recursively collect all descendant pages (breadth-first, returned flat)."""
    descendants = []
    queue = [page_id]

    while queue:
        current_id = queue.pop(0)
        response = confluence._session.get(
            f"{confluence.url}/rest/api/content/{current_id}/child/page",
            params={"limit": 200}
        )
        if response.status_code != 200:
            continue

        for child in response.json().get("results", []):
            child_info = {"id": child["id"], "title": child["title"]}
            descendants.append(child_info)
            queue.append(child["id"])

    return descendants
