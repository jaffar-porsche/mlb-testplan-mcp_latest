"""Comment operations for Jira issues."""
import logging

from fastapi import APIRouter, HTTPException

from client import jira
from config import JIRA_BASE_URL

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Comments"])


@router.post("/issue/{issue_key}/comments", summary="Add comment to Jira issue", operation_id="add_comment")
async def add_comment(issue_key: str, body: str, visibility: str = None):
    """
    Add a comment to a Jira issue.

    Parameters:
    - issue_key: The issue key (e.g., PROJ-123)
    - body: The comment text
    - visibility: Optional visibility restriction (e.g., "Developers", "Users")
    """
    try:
        issue = jira.issue(issue_key)
        comment = jira.add_comment(issue, body, visibility=visibility if visibility else None)

        return {
            "success": True,
            "message": f"Comment added successfully to {issue_key}",
            "comment": {
                "id": comment.id,
                "body": comment.body,
                "author": comment.author.displayName,
                "created": str(comment.created),
                "updated": str(comment.updated) if hasattr(comment, 'updated') else str(comment.created)
            },
            "issue_url": f"{JIRA_BASE_URL}/browse/{issue_key}"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to add comment: {e}")


@router.get("/issue/{issue_key}/comments", summary="Get comments from Jira issue", operation_id="get_comments")
async def get_comments(issue_key: str, max_results: int = 50):
    """
    Get all comments from a Jira issue.

    Parameters:
    - issue_key: The issue key (e.g., PROJ-123)
    - max_results: Maximum number of comments to return (default: 50)
    """
    try:
        issue = jira.issue(issue_key)
        comments = jira.comments(issue)

        if max_results > 0:
            comments = comments[-max_results:]

        comment_list = []
        for comment in comments:
            comment_data = {
                "id": comment.id,
                "body": comment.body,
                "author": {
                    "displayName": comment.author.displayName,
                    "accountId": getattr(comment.author, 'accountId', None),
                    "emailAddress": getattr(comment.author, 'emailAddress', None)
                },
                "created": str(comment.created),
                "updated": str(comment.updated) if hasattr(comment, 'updated') else str(comment.created)
            }

            if hasattr(comment, 'visibility') and comment.visibility:
                comment_data["visibility"] = {
                    "type": comment.visibility.type,
                    "value": comment.visibility.value
                }

            comment_list.append(comment_data)

        return {
            "issue_key": issue_key,
            "total_comments": len(comment_list),
            "comments": comment_list
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get comments: {e}")


@router.delete("/issue/{issue_key}/comments/{comment_id}", summary="Delete comment from Jira issue", operation_id="delete_comment")
async def delete_comment(issue_key: str, comment_id: str):
    """
    Delete a comment from a Jira issue.

    Parameters:
    - issue_key: The issue key (e.g., PROJ-123)
    - comment_id: The ID of the comment to delete
    """
    try:
        issue = jira.issue(issue_key)
        comment = jira.comment(issue_key, comment_id)
        comment.delete()

        return {
            "success": True,
            "message": f"Comment {comment_id} deleted from {issue_key}",
            "comment_id": comment_id,
            "issue_url": f"{JIRA_BASE_URL}/browse/{issue_key}"
        }

    except Exception as e:
        if "404" in str(e) or "not found" in str(e).lower():
            raise HTTPException(status_code=404, detail=f"Comment {comment_id} not found on {issue_key}")
        raise HTTPException(status_code=500, detail=f"Failed to delete comment: {e}")
