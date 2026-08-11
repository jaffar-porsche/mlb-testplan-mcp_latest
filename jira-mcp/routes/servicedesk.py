"""Jira Service Desk operations.

Provides read access to Service Desk requests (tickets) via the
``/rest/servicedeskapi`` REST API.  The standard Jira REST API
(``/rest/api/2/issue``) returns 403 for Service Desk projects because
they use a different permission model.  This module works around that
limitation by calling the Service Desk API directly with the same PAT.

Typical use-cases:
- View IT Security Audit requests (ITSA project)
- Read request status history and comments
- List available service desks
"""

import logging
from typing import Optional

import requests
from fastapi import APIRouter, HTTPException, Query

from client import http_session
from config import JIRA_SD_BASE, JIRA_BASE_URL

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Service Desk"])

_TIMEOUT = 15


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _sd_get(path: str, params: dict | None = None) -> requests.Response:
    """Authenticated GET against the Service Desk API."""
    url = f"{JIRA_SD_BASE}{path}"
    resp = http_session.get(url, params=params, timeout=_TIMEOUT)
    return resp


def _sd_post(path: str, json: dict) -> requests.Response:
    """Authenticated POST against the Service Desk API."""
    url = f"{JIRA_SD_BASE}{path}"
    resp = http_session.post(url, json=json, timeout=_TIMEOUT)
    return resp


def _format_date(date_obj: dict | None) -> str | None:
    """Extract friendly date string from SD date object."""
    if not date_obj:
        return None
    return date_obj.get("friendly") or date_obj.get("iso8601")


def _format_person(person: dict | None) -> dict | None:
    """Extract key person fields."""
    if not person:
        return None
    return {
        "displayName": person.get("displayName"),
        "emailAddress": person.get("emailAddress"),
        "username": person.get("name"),
        "active": person.get("active"),
    }


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@router.get(
    "/servicedesks",
    summary="List available Jira Service Desks",
    operation_id="list_servicedesks",
)
async def list_servicedesks(
    limit: int = Query(default=50, description="Max results per page"),
    start: int = Query(default=0, description="Pagination offset"),
):
    """List all Jira Service Desk portals accessible to the current user.

    Returns service desk ID, project key, and project name for each portal.
    Use the service desk ID with other endpoints if needed.
    """
    try:
        resp = _sd_get("/servicedesk", params={"limit": limit, "start": start})
        resp.raise_for_status()
        data = resp.json()
    except requests.RequestException as e:
        raise HTTPException(status_code=502, detail=f"Service Desk API error: {e}")

    desks = [
        {
            "id": d["id"],
            "projectKey": d.get("projectKey"),
            "projectName": d.get("projectName"),
        }
        for d in data.get("values", [])
    ]

    return {
        "total": data.get("size", len(desks)),
        "start": data.get("start", start),
        "isLastPage": data.get("isLastPage", True),
        "servicedesks": desks,
    }


@router.get(
    "/servicedesk/request/{request_key}",
    summary="Get Service Desk request details",
    operation_id="get_sd_request",
)
async def get_sd_request(request_key: str):
    """Retrieve details for a Jira Service Desk request.

    This works for tickets that return 403 via the standard Jira REST API
    (e.g. ITSA project tickets).  Returns request type, current status,
    status history, participants, and reporter.

    Parameters:
    - request_key: The issue key (e.g., ITSA-7571)
    """
    try:
        resp = _sd_get(
            f"/request/{request_key}",
            params={"expand": "requestType,serviceDesk,participant,status"},
        )
        if resp.status_code == 404:
            raise HTTPException(
                status_code=404,
                detail=f"Request {request_key} not found in any Service Desk.",
            )
        resp.raise_for_status()
        data = resp.json()
    except HTTPException:
        raise
    except requests.RequestException as e:
        raise HTTPException(status_code=502, detail=f"Service Desk API error: {e}")

    # Extract status history (newest first)
    status_history = []
    for s in data.get("status", {}).get("values", []):
        status_history.append(
            {
                "status": s.get("status"),
                "date": _format_date(s.get("statusDate")),
            }
        )

    # Extract participants
    participants = [
        _format_person(p) for p in data.get("participants", {}).get("values", [])
    ]

    # Request type info
    rt = data.get("requestType", {})
    sd = data.get("serviceDesk", {})

    # Build portal URL (browser-friendly)
    portal_url = (
        f"{JIRA_BASE_URL}/servicedesk/customer/portal/{sd.get('id', '?')}/{request_key}"
    )

    return {
        "issueKey": data.get("issueKey"),
        "issueId": data.get("issueId"),
        "currentStatus": data.get("currentStatus", {}).get("status"),
        "currentStatusDate": _format_date(
            data.get("currentStatus", {}).get("statusDate")
        ),
        "requestType": {
            "name": rt.get("name"),
            "description": rt.get("description"),
        },
        "serviceDesk": {
            "id": sd.get("id"),
            "projectKey": sd.get("projectKey"),
            "projectName": sd.get("projectName"),
        },
        "reporter": _format_person(data.get("reporter")),
        "createdDate": _format_date(data.get("createdDate")),
        "statusHistory": status_history,
        "participants": participants,
        "portalUrl": portal_url,
    }


@router.get(
    "/servicedesk/request/{request_key}/comments",
    summary="Get comments on a Service Desk request",
    operation_id="get_sd_request_comments",
)
async def get_sd_request_comments(
    request_key: str,
    public: bool = Query(
        default=True,
        description="If true, return only public (customer-visible) comments. "
        "Set to false to include internal comments.",
    ),
    limit: int = Query(default=50, description="Max comments to return"),
    start: int = Query(default=0, description="Pagination offset"),
):
    """Get comments on a Jira Service Desk request.

    Parameters:
    - request_key: The issue key (e.g., ITSA-7571)
    - public: Filter to public comments only (default true)
    - limit: Max number of comments
    - start: Pagination offset
    """
    try:
        resp = _sd_get(
            f"/request/{request_key}/comment",
            params={"public": str(public).lower(), "start": start, "limit": limit},
        )
        if resp.status_code == 404:
            raise HTTPException(
                status_code=404,
                detail=f"Request {request_key} not found.",
            )
        resp.raise_for_status()
        data = resp.json()
    except HTTPException:
        raise
    except requests.RequestException as e:
        raise HTTPException(status_code=502, detail=f"Service Desk API error: {e}")

    comments = []
    for c in data.get("values", []):
        comments.append(
            {
                "id": c.get("id"),
                "body": c.get("body"),
                "public": c.get("public"),
                "author": _format_person(c.get("author")),
                "created": _format_date(c.get("created")),
            }
        )

    return {
        "requestKey": request_key,
        "total": data.get("size", len(comments)),
        "isLastPage": data.get("isLastPage", True),
        "comments": comments,
    }


@router.post(
    "/servicedesk/request/{request_key}/comments",
    summary="Add comment to a Service Desk request",
    operation_id="add_sd_request_comment",
)
async def add_sd_request_comment(
    request_key: str,
    body: str = Query(description="The comment text"),
    public: bool = Query(
        default=True,
        description="If true, the comment is visible to the customer. "
        "If false, it is an internal comment.",
    ),
):
    """Add a comment to a Jira Service Desk request.

    This uses the Service Desk API which works for tickets that return 403
    via the standard Jira REST API (e.g. SUPPHW, ITSA projects).

    Parameters:
    - request_key: The issue key (e.g., SUPPHW-97147)
    - body: The comment text
    - public: Whether the comment is visible to the customer (default true)
    """
    try:
        resp = _sd_post(
            f"/request/{request_key}/comment",
            json={"body": body, "public": public},
        )
        if resp.status_code == 404:
            raise HTTPException(
                status_code=404,
                detail=f"Request {request_key} not found.",
            )
        resp.raise_for_status()
        data = resp.json()
    except HTTPException:
        raise
    except requests.RequestException as e:
        raise HTTPException(status_code=502, detail=f"Service Desk API error: {e}")

    return {
        "success": True,
        "message": f"Comment added to {request_key}",
        "comment": {
            "id": data.get("id"),
            "body": data.get("body"),
            "public": data.get("public"),
            "author": _format_person(data.get("author")),
            "created": _format_date(data.get("created")),
        },
    }


@router.get(
    "/servicedesk/requests",
    summary="Search Service Desk requests",
    operation_id="search_sd_requests",
)
async def search_sd_requests(
    service_desk_id: Optional[str] = Query(
        default=None,
        description="Filter by service desk ID (e.g., 2001 for IT Systemabsicherung). "
        "Omit to search across all service desks.",
    ),
    request_ownership: str = Query(
        default="OWNED_REQUESTS",
        description="Filter by ownership: "
        "OWNED_REQUESTS (requests you created/reported - default), "
        "PARTICIPATED_REQUESTS (requests where you are a participant, excludes reporter-only), "
        "ALL_REQUESTS (requests where you are creator or participant).",
    ),
    request_status: Optional[str] = Query(
        default=None,
        description="Filter by status: OPEN_REQUESTS, CLOSED_REQUESTS, "
        "ALL_REQUESTS. Omit to return all.",
    ),
    search_term: Optional[str] = Query(
        default=None,
        description="Text to search for in request summaries",
    ),
    limit: int = Query(default=25, description="Max results"),
    start: int = Query(default=0, description="Pagination offset"),
):
    """Search for Service Desk requests.

    Can filter by service desk, ownership, status, and search term.
    Useful for finding tickets in projects not accessible via the standard
    Jira REST API (e.g. ITSA).

    Defaults to OWNED_REQUESTS which returns requests where the authenticated
    user is the creator/reporter (equivalent to ``reporter=me`` in the
    Service Desk portal).
    """
    params = {
        "requestOwnership": request_ownership,
        "start": start,
        "limit": limit,
    }
    if request_status:
        params["requestStatus"] = request_status
    if search_term:
        params["searchTerm"] = search_term
    if service_desk_id:
        params["serviceDeskId"] = service_desk_id

    try:
        resp = _sd_get("/request", params=params)
        resp.raise_for_status()
        data = resp.json()
    except requests.RequestException as e:
        raise HTTPException(status_code=502, detail=f"Service Desk API error: {e}")

    results = []
    for req in data.get("values", []):
        results.append(
            {
                "issueKey": req.get("issueKey"),
                "issueId": req.get("issueId"),
                "currentStatus": req.get("currentStatus", {}).get("status"),
                "reporter": _format_person(req.get("reporter")),
                "createdDate": _format_date(req.get("createdDate")),
            }
        )

    return {
        "total": data.get("size", len(results)),
        "start": data.get("start", start),
        "isLastPage": data.get("isLastPage", True),
        "requests": results,
    }
