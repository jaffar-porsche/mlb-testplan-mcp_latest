"""Sprint management operations."""

import logging
from typing import List

from fastapi import APIRouter, HTTPException, Body

from client import http_session
from config import JIRA_AGILE_BASE

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Sprints"])


@router.get(
    "/sprint/{sprint_id}", summary="Get sprint details", operation_id="get_sprint"
)
async def get_sprint(sprint_id: str):
    """
    Get detailed information about a specific sprint.

    Parameters:
    - sprint_id: The sprint ID

    Returns sprint details including:
    - name, state (active/future/closed)
    - startDate, endDate, completeDate
    - goal (sprint goal text)
    - originBoardId
    """
    try:
        response = http_session.get(
            f"{JIRA_AGILE_BASE}/sprint/{sprint_id}",
        )

        if response.status_code == 404:
            raise HTTPException(status_code=404, detail=f"Sprint {sprint_id} not found")
        response.raise_for_status()

        sprint = response.json()
        return {
            "id": sprint.get("id"),
            "name": sprint.get("name"),
            "state": sprint.get("state"),
            "startDate": sprint.get("startDate"),
            "endDate": sprint.get("endDate"),
            "completeDate": sprint.get("completeDate"),
            "goal": sprint.get("goal"),
            "originBoardId": sprint.get("originBoardId"),
            "self": sprint.get("self"),
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get sprint: {e}")


@router.post(
    "/sprint/{sprint_id}/issue",
    summary="Move issues to sprint",
    operation_id="move_issues_to_sprint",
)
async def move_issues_to_sprint(
    sprint_id: str, issue_keys: List[str] = Body(..., embed=True)
):
    """
    Move one or more issues to a sprint.

    Parameters:
    - sprint_id: The target sprint ID
    - issue_keys: List of issue keys to move (e.g., ["PROJ-123", "PROJ-456"])

    Note: Issues will be added to the sprint. If they were in another sprint,
    they will be moved to this sprint.
    """
    try:
        response = http_session.post(
            f"{JIRA_AGILE_BASE}/sprint/{sprint_id}/issue",
            json={"issues": issue_keys},
        )

        if response.status_code == 404:
            raise HTTPException(status_code=404, detail=f"Sprint {sprint_id} not found")
        elif response.status_code == 400:
            error_detail = response.json() if response.content else "Bad request"
            raise HTTPException(
                status_code=400, detail=f"Failed to move issues: {error_detail}"
            )
        response.raise_for_status()

        return {
            "success": True,
            "message": f"Moved {len(issue_keys)} issue(s) to sprint {sprint_id}",
            "sprint_id": sprint_id,
            "issues": issue_keys,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to move issues to sprint: {e}"
        )


@router.delete(
    "/sprint/{sprint_id}/issue",
    summary="Remove issues from sprint",
    operation_id="remove_issues_from_sprint",
)
async def remove_issues_from_sprint(
    sprint_id: str, issue_keys: List[str] = Body(..., embed=True)
):
    """
    Remove issues from a sprint (move to backlog).

    Parameters:
    - sprint_id: The sprint ID (for context; issues are moved to backlog regardless)
    - issue_keys: List of issue keys to remove (e.g., ["PROJ-123", "PROJ-456"])

    Note: This moves issues to the backlog. They will no longer be in any sprint.
    """
    try:
        response = http_session.post(
            f"{JIRA_AGILE_BASE}/backlog/issue",
            json={"issues": issue_keys},
        )

        if response.status_code == 400:
            error_detail = response.json() if response.content else "Bad request"
            raise HTTPException(
                status_code=400, detail=f"Failed to remove issues: {error_detail}"
            )
        response.raise_for_status()

        return {
            "success": True,
            "message": f"Removed {len(issue_keys)} issue(s) from sprint to backlog",
            "sprint_id": sprint_id,
            "issues": issue_keys,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to remove issues from sprint: {e}"
        )
