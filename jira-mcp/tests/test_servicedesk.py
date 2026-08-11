"""Tests for Service Desk route module."""

import pytest
from unittest.mock import patch, MagicMock

from fastapi.testclient import TestClient


@pytest.fixture
def client():
    """Create a test client with mocked jira client."""
    from mcp_server import app

    return TestClient(app)


# ---------------------------------------------------------------------------
# Route registration
# ---------------------------------------------------------------------------


def test_servicedesk_router_has_routes():
    """Test servicedesk router has expected routes."""
    from routes.servicedesk import router

    paths = [route.path for route in router.routes]

    assert "/servicedesks" in paths
    assert "/servicedesk/request/{request_key}" in paths
    assert "/servicedesk/request/{request_key}/comments" in paths
    assert "/servicedesk/requests" in paths

    # Verify POST route exists for adding comments
    methods = {(route.path, list(route.methods)[0]) for route in router.routes if hasattr(route, "methods")}
    assert ("/servicedesk/request/{request_key}/comments", "POST") in methods


def test_servicedesk_router_is_registered():
    """Test servicedesk router is importable from routes package."""
    from routes import servicedesk_router

    assert servicedesk_router is not None


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------


def test_format_date_with_dict():
    """Test _format_date extracts friendly date."""
    from routes.servicedesk import _format_date

    result = _format_date(
        {"friendly": "24/Oct/2025 15:18", "iso8601": "2025-10-24T15:18:44+0200"}
    )
    assert result == "24/Oct/2025 15:18"


def test_format_date_fallback_to_iso():
    """Test _format_date falls back to iso8601 when friendly is missing."""
    from routes.servicedesk import _format_date

    result = _format_date({"iso8601": "2025-10-24T15:18:44+0200"})
    assert result == "2025-10-24T15:18:44+0200"


def test_format_date_with_none():
    """Test _format_date handles None."""
    from routes.servicedesk import _format_date

    assert _format_date(None) is None


def test_format_person_with_dict():
    """Test _format_person extracts correct fields."""
    from routes.servicedesk import _format_person

    result = _format_person(
        {
            "displayName": "Matheja, Ben (FDC2)",
            "emailAddress": "ben.matheja@porsche.de",
            "name": "P341939",
            "active": True,
        }
    )
    assert result["displayName"] == "Matheja, Ben (FDC2)"
    assert result["emailAddress"] == "ben.matheja@porsche.de"
    assert result["username"] == "P341939"
    assert result["active"] is True


def test_format_person_with_none():
    """Test _format_person handles None."""
    from routes.servicedesk import _format_person

    assert _format_person(None) is None


# ---------------------------------------------------------------------------
# GET /servicedesks
# ---------------------------------------------------------------------------


@patch("routes.servicedesk._sd_get")
def test_list_servicedesks(mock_get, client):
    """Test listing service desks."""
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.raise_for_status = MagicMock()
    mock_resp.json.return_value = {
        "size": 2,
        "start": 0,
        "isLastPage": True,
        "values": [
            {"id": "2001", "projectKey": "ITSA", "projectName": "IT Systemabsicherung"},
            {"id": "741", "projectKey": "CCCAH", "projectName": "Connect Helpdesk"},
        ],
    }
    mock_get.return_value = mock_resp

    response = client.get("/servicedesks?limit=10")

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    assert len(data["servicedesks"]) == 2
    assert data["servicedesks"][0]["projectKey"] == "ITSA"
    mock_get.assert_called_once_with("/servicedesk", params={"limit": 10, "start": 0})


# ---------------------------------------------------------------------------
# GET /servicedesk/request/{key}
# ---------------------------------------------------------------------------


@patch("routes.servicedesk._sd_get")
def test_get_sd_request(mock_get, client):
    """Test getting a Service Desk request."""
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.raise_for_status = MagicMock()
    mock_resp.json.return_value = {
        "issueKey": "ITSA-7571",
        "issueId": "6173343",
        "currentStatus": {
            "status": "SDE-Termin und Wrap-up",
            "statusDate": {"friendly": "15/Jan/2026 23:04"},
        },
        "requestType": {
            "name": "Sicherheitsfreigabe (DE)",
            "description": "IT security clearance",
        },
        "serviceDesk": {
            "id": "2001",
            "projectKey": "ITSA",
            "projectName": "IT Systemabsicherung",
        },
        "reporter": {
            "displayName": "Matheja, Ben (FDC2)",
            "emailAddress": "ben@test.de",
            "name": "P341939",
            "active": True,
        },
        "createdDate": {"friendly": "24/Oct/2025 15:18"},
        "status": {
            "values": [
                {
                    "status": "SDE-Termin und Wrap-up",
                    "statusDate": {"friendly": "15/Jan/2026 23:04"},
                },
                {"status": "Created", "statusDate": {"friendly": "24/Oct/2025 15:18"}},
            ]
        },
        "participants": {
            "values": [
                {
                    "displayName": "Hemminger, Dirk (FDC2)",
                    "emailAddress": "dirk@test.de",
                    "name": "P328191",
                    "active": True,
                },
            ]
        },
    }
    mock_get.return_value = mock_resp

    response = client.get("/servicedesk/request/ITSA-7571")

    assert response.status_code == 200
    data = response.json()
    assert data["issueKey"] == "ITSA-7571"
    assert data["currentStatus"] == "SDE-Termin und Wrap-up"
    assert data["requestType"]["name"] == "Sicherheitsfreigabe (DE)"
    assert data["reporter"]["displayName"] == "Matheja, Ben (FDC2)"
    assert len(data["statusHistory"]) == 2
    assert len(data["participants"]) == 1
    assert data["participants"][0]["displayName"] == "Hemminger, Dirk (FDC2)"


@patch("routes.servicedesk._sd_get")
def test_get_sd_request_not_found(mock_get, client):
    """Test 404 when request doesn't exist."""
    mock_resp = MagicMock()
    mock_resp.status_code = 404
    mock_get.return_value = mock_resp

    response = client.get("/servicedesk/request/ITSA-99999")

    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


# ---------------------------------------------------------------------------
# GET /servicedesk/request/{key}/comments
# ---------------------------------------------------------------------------


@patch("routes.servicedesk._sd_get")
def test_get_sd_request_comments(mock_get, client):
    """Test getting comments on a Service Desk request."""
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.raise_for_status = MagicMock()
    mock_resp.json.return_value = {
        "size": 2,
        "isLastPage": True,
        "values": [
            {
                "id": "9155464",
                "body": "Please authorize the group",
                "public": True,
                "author": {
                    "displayName": "Info Sec Robot",
                    "emailAddress": "robot@test.de",
                    "name": "ITSA.Robot",
                    "active": True,
                },
                "created": {"friendly": "24/Oct/2025 15:19"},
            },
            {
                "id": "9155470",
                "body": "We need to clarify Gesamtschutzbedarf first",
                "public": True,
                "author": {
                    "displayName": "Matheja, Ben (FDC2)",
                    "emailAddress": "ben@test.de",
                    "name": "P341939",
                    "active": True,
                },
                "created": {"friendly": "19/Dec/2025 08:34"},
            },
        ],
    }
    mock_get.return_value = mock_resp

    response = client.get("/servicedesk/request/ITSA-7571/comments?limit=10")

    assert response.status_code == 200
    data = response.json()
    assert data["requestKey"] == "ITSA-7571"
    assert data["total"] == 2
    assert len(data["comments"]) == 2
    assert data["comments"][0]["author"]["displayName"] == "Info Sec Robot"
    assert data["comments"][1]["body"] == "We need to clarify Gesamtschutzbedarf first"
    mock_get.assert_called_once_with(
        "/request/ITSA-7571/comment",
        params={"public": "true", "start": 0, "limit": 10},
    )


@patch("routes.servicedesk._sd_get")
def test_get_sd_request_comments_not_found(mock_get, client):
    """Test 404 when request doesn't exist for comments."""
    mock_resp = MagicMock()
    mock_resp.status_code = 404
    mock_get.return_value = mock_resp

    response = client.get("/servicedesk/request/ITSA-99999/comments")

    assert response.status_code == 404


# ---------------------------------------------------------------------------
# POST /servicedesk/request/{key}/comments
# ---------------------------------------------------------------------------


@patch("routes.servicedesk._sd_post")
def test_add_sd_request_comment(mock_post, client):
    """Test adding a comment to a Service Desk request."""
    mock_resp = MagicMock()
    mock_resp.status_code = 201
    mock_resp.raise_for_status = MagicMock()
    mock_resp.json.return_value = {
        "id": "9200001",
        "body": "Token bitte deaktivieren",
        "public": True,
        "author": {
            "displayName": "Matheja, Ben (FDC2)",
            "emailAddress": "ben@test.de",
            "name": "P341939",
            "active": True,
        },
        "created": {"friendly": "30/Mar/2026 09:15"},
    }
    mock_post.return_value = mock_resp

    response = client.post(
        "/servicedesk/request/SUPPHW-97147/comments?body=Token+bitte+deaktivieren&public=true"
    )

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["comment"]["id"] == "9200001"
    assert data["comment"]["body"] == "Token bitte deaktivieren"
    assert data["comment"]["public"] is True
    assert data["comment"]["author"]["username"] == "P341939"
    mock_post.assert_called_once_with(
        "/request/SUPPHW-97147/comment",
        json={"body": "Token bitte deaktivieren", "public": True},
    )


@patch("routes.servicedesk._sd_post")
def test_add_sd_request_comment_not_found(mock_post, client):
    """Test 404 when request doesn't exist for adding comment."""
    mock_resp = MagicMock()
    mock_resp.status_code = 404
    mock_post.return_value = mock_resp

    response = client.post(
        "/servicedesk/request/ITSA-99999/comments?body=test"
    )

    assert response.status_code == 404


@patch("routes.servicedesk._sd_post")
def test_add_sd_request_comment_internal(mock_post, client):
    """Test adding an internal (non-public) comment."""
    mock_resp = MagicMock()
    mock_resp.status_code = 201
    mock_resp.raise_for_status = MagicMock()
    mock_resp.json.return_value = {
        "id": "9200002",
        "body": "Internal note",
        "public": False,
        "author": {
            "displayName": "Matheja, Ben (FDC2)",
            "emailAddress": "ben@test.de",
            "name": "P341939",
            "active": True,
        },
        "created": {"friendly": "30/Mar/2026 09:20"},
    }
    mock_post.return_value = mock_resp

    response = client.post(
        "/servicedesk/request/SUPPHW-97147/comments?body=Internal+note&public=false"
    )

    assert response.status_code == 200
    data = response.json()
    assert data["comment"]["public"] is False
    mock_post.assert_called_once_with(
        "/request/SUPPHW-97147/comment",
        json={"body": "Internal note", "public": False},
    )


# ---------------------------------------------------------------------------
# GET /servicedesk/requests
# ---------------------------------------------------------------------------


@patch("routes.servicedesk._sd_get")
def test_search_sd_requests(mock_get, client):
    """Test searching Service Desk requests."""
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.raise_for_status = MagicMock()
    mock_resp.json.return_value = {
        "size": 1,
        "start": 0,
        "isLastPage": True,
        "values": [
            {
                "issueKey": "ITSA-7571",
                "issueId": "6173343",
                "currentStatus": {"status": "SDE-Termin und Wrap-up"},
                "reporter": {
                    "displayName": "Matheja, Ben (FDC2)",
                    "emailAddress": "ben@test.de",
                    "name": "P341939",
                    "active": True,
                },
                "createdDate": {"friendly": "24/Oct/2025 15:18"},
            },
        ],
    }
    mock_get.return_value = mock_resp

    response = client.get("/servicedesk/requests?service_desk_id=2001&limit=10")

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["requests"][0]["issueKey"] == "ITSA-7571"
    mock_get.assert_called_once_with(
        "/request",
        params={
            "requestOwnership": "OWNED_REQUESTS",
            "start": 0,
            "limit": 10,
            "serviceDeskId": "2001",
        },
    )


@patch("routes.servicedesk._sd_get")
def test_search_sd_requests_with_status_filter(mock_get, client):
    """Test searching with request status filter."""
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.raise_for_status = MagicMock()
    mock_resp.json.return_value = {
        "size": 0,
        "start": 0,
        "isLastPage": True,
        "values": [],
    }
    mock_get.return_value = mock_resp

    response = client.get("/servicedesk/requests?request_status=OPEN_REQUESTS")

    assert response.status_code == 200
    call_params = mock_get.call_args[1]["params"]
    assert call_params["requestStatus"] == "OPEN_REQUESTS"


@patch("routes.servicedesk._sd_get")
def test_search_sd_requests_with_search_term(mock_get, client):
    """Test searching with text search term."""
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.raise_for_status = MagicMock()
    mock_resp.json.return_value = {
        "size": 0,
        "start": 0,
        "isLastPage": True,
        "values": [],
    }
    mock_get.return_value = mock_resp

    response = client.get("/servicedesk/requests?search_term=security")

    assert response.status_code == 200
    call_params = mock_get.call_args[1]["params"]
    assert call_params["searchTerm"] == "security"


# ---------------------------------------------------------------------------
# Error handling
# ---------------------------------------------------------------------------


@patch("routes.servicedesk._sd_get")
def test_list_servicedesks_api_error(mock_get, client):
    """Test error handling when SD API fails."""
    import requests as req

    mock_get.side_effect = req.RequestException("Connection refused")

    response = client.get("/servicedesks")

    assert response.status_code == 502
    assert "Service Desk API error" in response.json()["detail"]
