"""Project and board operations."""

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException

from client import jira
from config import JIRA_BASE_URL

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Projects"])


@router.get("/projects", summary="List all Jira projects", operation_id="list_projects")
async def list_projects():
    """Get a list of all Jira projects accessible to the current user."""
    try:
        projects = jira.projects()

        project_list = []
        for project in projects:
            project_data = {
                "key": project.key,
                "name": project.name,
                "id": project.id,
                "projectTypeKey": getattr(project, "projectTypeKey", None),
                "lead": {
                    "displayName": project.lead.displayName
                    if hasattr(project, "lead") and project.lead
                    else "Unknown",
                    "accountId": getattr(project.lead, "accountId", None)
                    if hasattr(project, "lead") and project.lead
                    else None,
                },
                "url": f"{JIRA_BASE_URL}/browse/{project.key}",
            }

            if hasattr(project, "description") and project.description:
                project_data["description"] = project.description

            project_list.append(project_data)

        return {"total_projects": len(project_list), "projects": project_list}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list projects: {e}")


@router.get(
    "/project/{project_key}",
    summary="Get Jira project details",
    operation_id="get_project",
)
async def get_project_details(project_key: str):
    """
    Get detailed information about a specific Jira project.

    Parameters:
    - project_key: The project key (e.g., SLIM, DEVX)
    """
    try:
        project = jira.project(project_key)

        project_data = {
            "key": project.key,
            "name": project.name,
            "id": project.id,
            "description": getattr(project, "description", None),
            "projectTypeKey": getattr(project, "projectTypeKey", None),
            "lead": {
                "displayName": project.lead.displayName
                if hasattr(project, "lead") and project.lead
                else "Unknown",
                "accountId": getattr(project.lead, "accountId", None)
                if hasattr(project, "lead") and project.lead
                else None,
                "emailAddress": getattr(project.lead, "emailAddress", None)
                if hasattr(project, "lead") and project.lead
                else None,
            },
            "url": f"{JIRA_BASE_URL}/browse/{project.key}",
        }

        # Get components
        try:
            components = jira.project_components(project)
            project_data["components"] = [
                {
                    "id": comp.id,
                    "name": comp.name,
                    "description": getattr(comp, "description", None),
                    "lead": comp.lead.displayName
                    if hasattr(comp, "lead") and comp.lead
                    else None,
                }
                for comp in components
            ]
        except Exception as e:
            logger.warning(f"Failed to get components for project {project_key}: {e}")
            project_data["components"] = []

        # Get versions
        try:
            versions = jira.project_versions(project)
            project_data["versions"] = [
                {
                    "id": ver.id,
                    "name": ver.name,
                    "description": getattr(ver, "description", None),
                    "released": getattr(ver, "released", False),
                    "releaseDate": str(ver.releaseDate)
                    if hasattr(ver, "releaseDate") and ver.releaseDate
                    else None,
                }
                for ver in versions
            ]
        except Exception as e:
            logger.warning(f"Failed to get versions for project {project_key}: {e}")
            project_data["versions"] = []

        return project_data

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get project details: {e}"
        )


@router.get("/boards", summary="List all Jira boards", operation_id="list_boards")
async def get_boards():
    """Get a list of all Jira boards (Agile boards) accessible to the current user."""
    try:
        boards = jira.boards()

        board_list = []
        for board in boards:
            board_data = {
                "id": board.id,
                "name": board.name,
                "type": getattr(board, "type", None),
                "self": getattr(board, "self", None),
            }

            if hasattr(board, "location"):
                board_data["location"] = {
                    "projectId": getattr(board.location, "projectId", None),
                    "projectKey": getattr(board.location, "projectKey", None),
                    "projectName": getattr(board.location, "projectName", None),
                }

            board_list.append(board_data)

        return {"total_boards": len(board_list), "boards": board_list}

    except AttributeError:
        raise HTTPException(
            status_code=501, detail="Agile boards not supported in this JIRA instance"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list boards: {e}")


@router.get(
    "/board/{board_id}/sprints",
    summary="Get sprints from Jira board",
    operation_id="get_board_sprints",
)
async def get_board_sprints(board_id: str, state: Optional[str] = None):
    """
    Get all sprints from a specific Jira board.

    Parameters:
    - board_id: The board ID
    - state: Filter by sprint state ("active", "future", "closed")
    """
    try:
        params = {"maxResults": 50}
        if state:
            params["state"] = state

        from client import http_session
        from config import JIRA_AGILE_BASE

        response = http_session.get(
            f"{JIRA_AGILE_BASE}/board/{board_id}/sprint",
            params=params,
        )

        if response.status_code == 404:
            raise HTTPException(status_code=404, detail=f"Board {board_id} not found")
        if response.status_code == 400:
            try:
                error_detail = response.json()
            except Exception:
                error_detail = response.text
            raise HTTPException(
                status_code=400,
                detail=f"Board {board_id} does not support sprints (likely a Kanban or Portfolio board). Jira response: {error_detail}"
            )
        response.raise_for_status()

        data = response.json()
        sprints = data.get("values", [])

        sprint_list = []
        for sprint in sprints:
            sprint_data = {
                "id": sprint.get("id"),
                "name": sprint.get("name"),
                "state": sprint.get("state"),
                "startDate": sprint.get("startDate"),
                "endDate": sprint.get("endDate"),
                "completeDate": sprint.get("completeDate"),
                "originBoardId": sprint.get("originBoardId"),
                "self": sprint.get("self"),
            }

            if sprint.get("goal"):
                sprint_data["goal"] = sprint.get("goal")

            sprint_list.append(sprint_data)

        return {
            "board_id": board_id,
            "total_sprints": len(sprint_list),
            "sprints": sprint_list,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get sprints: {e}")
