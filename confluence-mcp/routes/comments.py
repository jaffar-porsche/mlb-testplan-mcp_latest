"""Comment operations for Confluence pages."""
import logging

from fastapi import APIRouter, HTTPException

from client import confluence
from config import CONFLUENCE_BASE_URL
from models import AddCommentRequest
from html_utils import sanitize_html_for_confluence

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Comments"])


@router.post("/page/{page_id}/comments", summary="Add comment to Confluence page", operation_id="add_comment")
async def add_comment(page_id: str, request: AddCommentRequest):
    """
    Add a comment to a Confluence page.

    Parameters:
    - page_id: The page ID (e.g., "2347613274")
    - body: The comment text (Confluence storage format HTML or plain text)
    """
    try:
        sanitized_body = sanitize_html_for_confluence(request.body)

        comment_data = {
            "type": "comment",
            "container": {"id": page_id, "type": "page"},
            "body": {
                "storage": {
                    "value": sanitized_body,
                    "representation": "storage"
                }
            }
        }

        response = confluence._session.post(
            f"{confluence.url}/rest/api/content",
            json=comment_data,
            headers={"Content-Type": "application/json"}
        )

        if response.status_code in (200, 201):
            comment = response.json()
            return {
                "success": True,
                "comment": {
                    "id": comment["id"],
                    "body": comment["body"]["storage"]["value"],
                    "author": comment.get("version", {}).get("by", {}).get("displayName", "Unknown"),
                    "created": comment.get("version", {}).get("when", ""),
                },
                "page_id": page_id,
                "page_url": f"{CONFLUENCE_BASE_URL}/pages/viewpage.action?pageId={page_id}"
            }
        else:
            raise ValueError(f"API returned {response.status_code}: {response.text}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to add comment to page {page_id}: {e}")


@router.get("/page/{page_id}/comments", summary="Get comments from Confluence page", operation_id="get_comments")
async def get_comments(page_id: str, limit: int = 25):
    """
    Get all comments from a Confluence page.

    Parameters:
    - page_id: The page ID (e.g., "2347613274")
    - limit: Maximum number of comments to return (default: 25)
    """
    try:
        response = confluence._session.get(
            f"{confluence.url}/rest/api/content/{page_id}/child/comment",
            params={
                "limit": limit,
                "expand": "body.storage,version",
                "depth": "all"
            }
        )

        if response.status_code != 200:
            raise ValueError(f"API returned {response.status_code}: {response.text}")

        data = response.json()
        comments = []

        for comment in data.get("results", []):
            version = comment.get("version", {})
            comments.append({
                "id": comment["id"],
                "body": comment.get("body", {}).get("storage", {}).get("value", ""),
                "author": version.get("by", {}).get("displayName", "Unknown"),
                "created": version.get("when", ""),
            })

        return {
            "page_id": page_id,
            "total": data.get("size", len(comments)),
            "comments": comments
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get comments for page {page_id}: {e}")


@router.delete("/page/{page_id}/comments/{comment_id}", summary="Delete comment from Confluence page", operation_id="delete_comment")
async def delete_comment(page_id: str, comment_id: str):
    """
    Delete a comment from a Confluence page.

    Parameters:
    - page_id: The page ID (for context)
    - comment_id: The comment ID to delete
    """
    try:
        response = confluence._session.delete(
            f"{confluence.url}/rest/api/content/{comment_id}"
        )

        if response.status_code == 204:
            return {
                "success": True,
                "message": f"Comment {comment_id} deleted from page {page_id}"
            }
        else:
            raise ValueError(f"API returned {response.status_code}: {response.text}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete comment {comment_id}: {e}")
