"""Tests for remote link endpoints."""

import pytest
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient


@pytest.fixture
def client():
    """Create a test client with mocked jira client."""
    from mcp_server import app

    return TestClient(app)


def test_remote_links_router_has_routes():
    """Test remote links router has expected routes."""
    from routes.remote_links import router

    paths = [route.path for route in router.routes]
    methods = {route.path: route.methods for route in router.routes}

    assert "/issue/{issue_key}/remotelink" in paths
    assert "/issue/{issue_key}/remotelink/{link_id}" in paths
    assert "DELETE" in methods["/issue/{issue_key}/remotelink/{link_id}"]


@patch("routes.remote_links.http_session")
def test_list_remote_links(mock_session, client):
    """Test listing remote links on an issue."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = [
        {
            "id": 10001,
            "relationship": "Release Page",
            "object": {
                "url": "https://example.com/release/1.0",
                "title": "Release 1.0",
                "icon": {"url16x16": "https://example.com/icon.png"},
            },
        },
        {
            "id": 10002,
            "object": {
                "url": "https://example.com/docs",
                "title": "Documentation",
            },
        },
    ]
    mock_session.get.return_value = mock_response

    response = client.get("/issue/PROJ-123/remotelink")

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    assert data["issue_key"] == "PROJ-123"
    assert data["remote_links"][0]["id"] == 10001
    assert data["remote_links"][0]["url"] == "https://example.com/release/1.0"
    assert data["remote_links"][0]["title"] == "Release 1.0"
    assert data["remote_links"][0]["relationship"] == "Release Page"
    assert data["remote_links"][0]["icon_url"] == "https://example.com/icon.png"
    assert data["remote_links"][1]["icon_url"] is None


@patch("routes.remote_links.http_session")
def test_list_remote_links_empty(mock_session, client):
    """Test listing remote links when none exist."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = []
    mock_session.get.return_value = mock_response

    response = client.get("/issue/PROJ-123/remotelink")

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 0
    assert data["remote_links"] == []


@patch("routes.remote_links.http_session")
def test_list_remote_links_issue_not_found(mock_session, client):
    """Test listing remote links for non-existent issue."""
    mock_response = MagicMock()
    mock_response.status_code = 404
    mock_session.get.return_value = mock_response

    response = client.get("/issue/PROJ-999/remotelink")

    assert response.status_code == 404
    assert "not found" in response.json()["detail"]


@patch("routes.remote_links.http_session")
def test_create_remote_link(mock_session, client):
    """Test creating a remote link."""
    mock_response = MagicMock()
    mock_response.status_code = 201
    mock_response.json.return_value = {"id": 10001}
    mock_response.raise_for_status = MagicMock()
    mock_session.post.return_value = mock_response

    response = client.post(
        "/issue/PROJ-123/remotelink",
        json={
            "url": "https://example.com/release/1.0",
            "title": "Release 1.0",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["id"] == 10001
    assert data["issue_key"] == "PROJ-123"
    assert data["url"] == "https://example.com/release/1.0"

    # Verify payload sent to Jira
    call_kwargs = mock_session.post.call_args
    payload = call_kwargs.kwargs.get("json") or call_kwargs[1].get("json")
    assert payload["object"]["url"] == "https://example.com/release/1.0"
    assert payload["object"]["title"] == "Release 1.0"
    assert "icon" not in payload["object"]
    assert "relationship" not in payload


@patch("routes.remote_links.http_session")
def test_create_remote_link_with_icon_and_relationship(mock_session, client):
    """Test creating a remote link with optional fields."""
    mock_response = MagicMock()
    mock_response.status_code = 201
    mock_response.json.return_value = {"id": 10002}
    mock_response.raise_for_status = MagicMock()
    mock_session.post.return_value = mock_response

    response = client.post(
        "/issue/PROJ-123/remotelink",
        json={
            "url": "https://example.com/release/1.0",
            "title": "Release 1.0",
            "icon_url": "https://example.com/icon.png",
            "relationship": "Release Page",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True

    call_kwargs = mock_session.post.call_args
    payload = call_kwargs.kwargs.get("json") or call_kwargs[1].get("json")
    assert payload["object"]["icon"]["url16x16"] == "https://example.com/icon.png"
    assert payload["relationship"] == "Release Page"


@patch("routes.remote_links.http_session")
def test_create_remote_link_issue_not_found(mock_session, client):
    """Test creating a remote link on non-existent issue."""
    mock_response = MagicMock()
    mock_response.status_code = 404
    mock_session.post.return_value = mock_response

    response = client.post(
        "/issue/PROJ-999/remotelink",
        json={"url": "https://example.com", "title": "Test"},
    )

    assert response.status_code == 404


@patch("routes.remote_links.http_session")
def test_delete_remote_link(mock_session, client):
    """Test deleting a remote link."""
    mock_response = MagicMock()
    mock_response.status_code = 204
    mock_session.delete.return_value = mock_response

    response = client.delete("/issue/PROJ-123/remotelink/10001")

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["link_id"] == "10001"


@patch("routes.remote_links.http_session")
def test_delete_remote_link_not_found(mock_session, client):
    """Test deleting a non-existent remote link."""
    mock_response = MagicMock()
    mock_response.status_code = 404
    mock_session.delete.return_value = mock_response

    response = client.delete("/issue/PROJ-123/remotelink/99999")

    assert response.status_code == 404
    assert "not found" in response.json()["detail"]


@patch("routes.remote_links.http_session")
def test_list_remote_links_server_error(mock_session, client):
    """Test error handling when Jira API fails."""
    mock_session.get.side_effect = Exception("Connection refused")

    response = client.get("/issue/PROJ-123/remotelink")

    assert response.status_code == 500
    assert "Failed to list remote links" in response.json()["detail"]


# ---------------------------------------------------------------------------
# Live MCP integration test results (2026-03-13)
# ---------------------------------------------------------------------------
# Tested via OpenCode MCP tool calls against skyway.porsche.com/jira
# Target issue: DSWTEAMSYS-493
#
# 1. list_remote_links (empty)
#    Request:  list_remote_links(issue_key="DSWTEAMSYS-493")
#    Response: {"total": 0, "issue_key": "DSWTEAMSYS-493", "remote_links": []}
#    Result:   PASS
#
# 2. create_remote_link
#    Request:  create_remote_link(
#                issue_key="DSWTEAMSYS-493",
#                url="https://skyway.porsche.com/confluence/spaces/ARTDIAGUPD/pages/2380412407/...",
#                title="Confluence: GitLab to GitHub Migration Guide",
#                relationship="Documentation"
#              )
#    Response: {"success": true, "id": 1196369, "issue_key": "DSWTEAMSYS-493", ...}
#    Result:   PASS
#
# 3. list_remote_links (verify creation)
#    Request:  list_remote_links(issue_key="DSWTEAMSYS-493")
#    Response: {"total": 1, "remote_links": [{"id": 1196369, "relationship": "Documentation",
#               "url": "https://skyway.porsche.com/confluence/...", "title": "Confluence: ...",
#               "icon_url": null}]}
#    Result:   PASS
#
# 4. delete_remote_link
#    Request:  delete_remote_link(issue_key="DSWTEAMSYS-493", link_id="1196369")
#    Response: {"success": true, "message": "Remote link 1196369 deleted from DSWTEAMSYS-493",
#               "link_id": "1196369"}
#    Result:   PASS
#
# 5. list_remote_links (verify deletion)
#    Request:  list_remote_links(issue_key="DSWTEAMSYS-493")
#    Response: {"total": 0, "issue_key": "DSWTEAMSYS-493", "remote_links": []}
#    Result:   PASS
#
# All 5/5 tests passed. Full CRUD lifecycle verified via native MCP tool calls.
# ---------------------------------------------------------------------------
