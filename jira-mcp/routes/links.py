"""Issue linking operations."""

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from client import jira, http_session
from config import JIRA_BASE_URL


class CreateLinkRequest(BaseModel):
    """Request body for creating an issue link."""

    target_issue_key: str
    link_type: str
    direction: Optional[str] = "outward"


logger = logging.getLogger(__name__)
router = APIRouter(tags=["Issue Links"])


@router.get(
    "/link_types",
    summary="List all available issue link types",
    operation_id="list_link_types",
)
async def list_link_types():
    """
    List all available Jira issue link types.

    Returns link type information including:
    - id: Link type identifier
    - name: Link type name (e.g., "Blocks", "Relates")
    - inward: Inward description (e.g., "is blocked by")
    - outward: Outward description (e.g., "blocks")
    """
    try:
        link_types = jira.issue_link_types()
        return {
            "total": len(link_types),
            "link_types": [
                {
                    "id": lt.id,
                    "name": lt.name,
                    "inward": lt.inward,
                    "outward": lt.outward,
                }
                for lt in link_types
            ],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list link types: {e}")


@router.post(
    "/issue/{issue_key}/link",
    summary="Create link between two issues",
    operation_id="create_issue_link",
)
async def create_issue_link(issue_key: str, body: CreateLinkRequest):
    """
    Create a link between two Jira issues.

    Parameters:
    - issue_key: The source issue key (e.g., PROJ-123)
    - body.target_issue_key: The target issue key to link to
    - body.link_type: Link type name (e.g., "Blocks", "Relates", "Agile Hive Link")
    - body.direction: Link direction from source issue perspective
      - "outward": source -> target (e.g., "blocks")
      - "inward": target -> source (e.g., "is blocked by")

    Example: To create "PROJ-123 blocks PROJ-456":
      - issue_key: PROJ-123
      - target_issue_key: PROJ-456
      - link_type: Blocks
      - direction: outward
    """
    try:
        # Verify both issues exist
        jira.issue(issue_key)
        jira.issue(body.target_issue_key)

        # Create the link
        # For Agile Hive Link: inward="Parent of", outward="Child of"
        # - inwardIssue = the issue described by "inward" (Parent)
        # - outwardIssue = the issue described by "outward" (Child)
        # When direction="inward", source issue_key is the Parent
        if body.direction.lower() == "inward":
            jira.create_issue_link(
                type=body.link_type,
                inwardIssue=body.target_issue_key,  # Target is Child (described as Parent of source)
                outwardIssue=issue_key,  # Source is Parent (described as Child of target)
            )
        else:
            jira.create_issue_link(
                type=body.link_type,
                inwardIssue=issue_key,
                outwardIssue=body.target_issue_key,
            )

        return {
            "success": True,
            "message": f"Link created: {issue_key} -> {body.target_issue_key}",
            "link_type": body.link_type,
            "direction": body.direction,
            "source_issue": issue_key,
            "target_issue": body.target_issue_key,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create issue link: {e}")


@router.delete(
    "/issue/{issue_key}/link/{link_id}",
    summary="Delete issue link",
    operation_id="delete_issue_link",
)
async def delete_issue_link(issue_key: str, link_id: str):
    """
    Delete an issue link by its ID.

    Parameters:
    - issue_key: The issue key (for context/validation)
    - link_id: The link ID to delete (found in issue details under issuelinks)
    """
    try:
        response = http_session.delete(
            f"{JIRA_BASE_URL}/rest/api/2/issueLink/{link_id}",
        )

        if response.status_code == 204:
            return {
                "success": True,
                "message": f"Link {link_id} deleted from {issue_key}",
                "link_id": link_id,
            }
        elif response.status_code == 404:
            raise HTTPException(status_code=404, detail=f"Link {link_id} not found")
        else:
            response.raise_for_status()

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete issue link: {e}")
