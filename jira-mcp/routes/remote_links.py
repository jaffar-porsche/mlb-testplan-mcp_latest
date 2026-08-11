"""Remote link (web link) operations on Jira issues."""

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from client import http_session
from config import JIRA_BASE_URL


class CreateRemoteLinkRequest(BaseModel):
    """Request body for creating a remote link."""

    url: str
    title: str
    icon_url: Optional[str] = None
    relationship: Optional[str] = None


logger = logging.getLogger(__name__)
router = APIRouter(tags=["Remote Links"])


@router.get(
    "/issue/{issue_key}/remotelink",
    summary="List remote links on an issue",
    operation_id="list_remote_links",
)
async def list_remote_links(issue_key: str):
    """
    List all remote links (web links) on a Jira issue.

    Parameters:
    - issue_key: The issue key (e.g., PROJ-123)
    """
    try:
        response = http_session.get(
            f"{JIRA_BASE_URL}/rest/api/2/issue/{issue_key}/remotelink",
        )

        if response.status_code == 404:
            raise HTTPException(status_code=404, detail=f"Issue {issue_key} not found")

        response.raise_for_status()
        links = response.json()

        return {
            "total": len(links),
            "issue_key": issue_key,
            "remote_links": [
                {
                    "id": link.get("id"),
                    "relationship": link.get("relationship"),
                    "url": link.get("object", {}).get("url"),
                    "title": link.get("object", {}).get("title"),
                    "icon_url": link.get("object", {}).get("icon", {}).get("url16x16"),
                }
                for link in links
            ],
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list remote links: {e}")


@router.post(
    "/issue/{issue_key}/remotelink",
    summary="Add a remote link to an issue",
    operation_id="create_remote_link",
)
async def create_remote_link(issue_key: str, body: CreateRemoteLinkRequest):
    """
    Add a remote link (web link) to a Jira issue.

    Parameters:
    - issue_key: The issue key (e.g., PROJ-123)
    - body.url: The URL of the remote link
    - body.title: Display title for the link
    - body.icon_url: Optional URL for a 16x16 icon
    - body.relationship: Optional relationship description (e.g., "Release Page")
    """
    try:
        payload = {
            "object": {
                "url": body.url,
                "title": body.title,
            }
        }

        if body.icon_url:
            payload["object"]["icon"] = {"url16x16": body.icon_url}

        if body.relationship:
            payload["relationship"] = body.relationship

        response = http_session.post(
            f"{JIRA_BASE_URL}/rest/api/2/issue/{issue_key}/remotelink",
            json=payload,
        )

        if response.status_code == 404:
            raise HTTPException(status_code=404, detail=f"Issue {issue_key} not found")

        response.raise_for_status()
        result = response.json()

        return {
            "success": True,
            "message": f"Remote link added to {issue_key}",
            "id": result.get("id"),
            "issue_key": issue_key,
            "url": body.url,
            "title": body.title,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create remote link: {e}")


@router.delete(
    "/issue/{issue_key}/remotelink/{link_id}",
    summary="Delete a remote link from an issue",
    operation_id="delete_remote_link",
)
async def delete_remote_link(issue_key: str, link_id: str):
    """
    Delete a remote link from a Jira issue by its ID.

    Parameters:
    - issue_key: The issue key (for context)
    - link_id: The remote link ID to delete (found via list remote links)
    """
    try:
        response = http_session.delete(
            f"{JIRA_BASE_URL}/rest/api/2/issue/{issue_key}/remotelink/{link_id}",
        )

        if response.status_code == 204:
            return {
                "success": True,
                "message": f"Remote link {link_id} deleted from {issue_key}",
                "link_id": link_id,
            }
        elif response.status_code == 404:
            raise HTTPException(
                status_code=404, detail=f"Remote link {link_id} not found on {issue_key}"
            )
        else:
            response.raise_for_status()

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete remote link: {e}")
