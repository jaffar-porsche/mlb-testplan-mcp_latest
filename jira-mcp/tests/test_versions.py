"""Tests for version management endpoints (get_version_summary, update_version)."""

import pytest
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient


@pytest.fixture
def client():
    """Create a test client with mocked jira client."""
    from mcp_server import app

    return TestClient(app)


@pytest.fixture
def mock_version():
    """Create a mock Jira version object."""
    version = MagicMock()
    version.id = "110436"
    version.name = "JRV-25.37-7"
    version.description = "DB key rotation, Improvement of logging, NodeJS22"
    version.startDate = None
    version.releaseDate = "2025-11-03"
    version.released = True
    version.archived = False
    return version


@pytest.fixture
def mock_issues():
    """Create mock issues for version summary."""
    issues = []

    # Enabler
    enabler = MagicMock()
    enabler.key = "GFS-19598"
    enabler.fields.summary = "Rotate DB Credentials Prod"
    enabler.fields.status.name = "Closed"
    enabler.fields.issuetype.name = "Enabler"
    enabler.fields.priority.name = "Medium"
    issues.append(enabler)

    # Story 1
    story1 = MagicMock()
    story1.key = "GFS-18968"
    story1.fields.summary = "Upgrade all lambdas to NodeJS22"
    story1.fields.status.name = "Closed"
    story1.fields.issuetype.name = "Story"
    story1.fields.priority.name = "Medium"
    issues.append(story1)

    # Story 2
    story2 = MagicMock()
    story2.key = "GFS-19562"
    story2.fields.summary = "Logging for CRS in json format"
    story2.fields.status.name = "Closed"
    story2.fields.issuetype.name = "Story"
    story2.fields.priority.name = "High"
    issues.append(story2)

    return issues


# --- Route registration tests ---


def test_teams_router_has_version_summary_route():
    """Test teams router has the version summary route."""
    from routes.teams import router

    paths = [route.path for route in router.routes]
    assert "/versions/{version_id}/summary" in paths


def test_teams_router_has_update_version_route():
    """Test teams router has the update version route."""
    from routes.teams import router

    paths = [route.path for route in router.routes]
    methods = {route.path: route.methods for route in router.routes}

    assert "/versions/{version_id}" in paths
    assert "PUT" in methods["/versions/{version_id}"]


# --- get_version_summary tests ---


@patch("routes.teams.jira")
def test_get_version_summary_success(mock_jira, client, mock_version, mock_issues):
    """Test successful version summary extraction."""
    mock_jira.version.return_value = mock_version
    mock_jira.search_issues.return_value = mock_issues

    response = client.get("/versions/110436/summary?project_key=GFS")

    assert response.status_code == 200
    data = response.json()
    assert data["version_id"] == "110436"
    assert data["version_name"] == "JRV-25.37-7"
    assert data["project"] == "GFS"
    assert data["issue_count"] == 3
    assert data["issues_by_type"] == {"Enabler": 1, "Story": 2}
    assert data["truncated"] is False
    assert "Release JRV-25.37-7" in data["summary_text"]
    assert "GFS-19598" in data["summary_text"]
    assert "GFS-18968" in data["summary_text"]

    mock_jira.version.assert_called_once_with("110436")
    mock_jira.search_issues.assert_called_once()


@patch("routes.teams.jira")
def test_get_version_summary_groups_by_type(
    mock_jira, client, mock_version, mock_issues
):
    """Test that issues are grouped by type in the summary."""
    mock_jira.version.return_value = mock_version
    mock_jira.search_issues.return_value = mock_issues

    response = client.get("/versions/110436/summary?project_key=GFS")

    data = response.json()
    assert "Enabler (1):" in data["summary_text"]
    assert "Story (2):" in data["summary_text"]

    # Verify issues list has correct types
    issue_types = [i["issuetype"] for i in data["issues"]]
    assert issue_types.count("Enabler") == 1
    assert issue_types.count("Story") == 2


@patch("routes.teams.jira")
def test_get_version_summary_no_issues(mock_jira, client, mock_version):
    """Test version summary with no linked issues."""
    mock_jira.version.return_value = mock_version
    mock_jira.search_issues.return_value = []

    response = client.get("/versions/110436/summary?project_key=GFS")

    assert response.status_code == 200
    data = response.json()
    assert data["issue_count"] == 0
    assert data["issues_by_type"] == {}
    assert data["issues"] == []
    assert "Release JRV-25.37-7" in data["summary_text"]


@patch("routes.teams.jira")
def test_get_version_summary_custom_max_length(
    mock_jira, client, mock_version, mock_issues
):
    """Test max_length parameter is respected."""
    mock_jira.version.return_value = mock_version
    mock_jira.search_issues.return_value = mock_issues

    response = client.get("/versions/110436/summary?project_key=GFS&max_length=100")

    assert response.status_code == 200
    data = response.json()
    assert data["max_length"] == 100
    assert data["truncated"] is True
    assert data["summary_length"] <= 100


@patch("routes.teams.jira")
def test_get_version_summary_version_not_found(mock_jira, client):
    """Test error when version ID doesn't exist."""
    mock_jira.version.side_effect = Exception("Version not found")

    response = client.get("/versions/999999/summary?project_key=GFS")

    assert response.status_code == 500
    assert "Failed to fetch version" in response.json()["detail"]


@patch("routes.teams.jira")
def test_get_version_summary_search_error(mock_jira, client, mock_version):
    """Test error when issue search fails."""
    mock_jira.version.return_value = mock_version
    mock_jira.search_issues.side_effect = Exception("JQL syntax error")

    response = client.get("/versions/110436/summary?project_key=GFS")

    assert response.status_code == 500
    assert "Failed to search issues" in response.json()["detail"]


# --- update_version tests ---


@patch("routes.teams.jira")
def test_update_version_description(mock_jira, client, mock_version):
    """Test updating version description."""
    mock_jira.version.return_value = mock_version

    response = client.put("/versions/110436?description=New+release+description")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "110436"
    assert data["name"] == "JRV-25.37-7"
    assert "description" in data["updated_fields"]

    mock_jira.version.assert_called_once_with("110436")
    mock_version.update.assert_called_once_with(description="New release description")


@patch("routes.teams.jira")
def test_update_version_multiple_fields(mock_jira, client, mock_version):
    """Test updating multiple version fields at once."""
    mock_jira.version.return_value = mock_version

    response = client.put(
        "/versions/110436?description=Updated&released=false&release_date=2026-01-01"
    )

    assert response.status_code == 200
    data = response.json()
    assert set(data["updated_fields"]) == {"description", "released", "releaseDate"}

    mock_version.update.assert_called_once_with(
        description="Updated", released=False, releaseDate="2026-01-01"
    )


@patch("routes.teams.jira")
def test_update_version_no_fields(mock_jira, client):
    """Test error when no fields are provided."""
    response = client.put("/versions/110436")

    assert response.status_code == 400
    assert "No fields to update" in response.json()["detail"]


@patch("routes.teams.jira")
def test_update_version_jira_error(mock_jira, client):
    """Test error handling when Jira API fails."""
    mock_jira.version.side_effect = Exception("Permission denied")

    response = client.put("/versions/110436?description=test")

    assert response.status_code == 500
    assert "Failed to update version" in response.json()["detail"]


@patch("routes.teams.jira")
def test_update_version_name(mock_jira, client, mock_version):
    """Test updating version name only."""
    mock_jira.version.return_value = mock_version

    response = client.put("/versions/110436?name=JRV-25.37-7-renamed")

    assert response.status_code == 200
    data = response.json()
    assert "name" in data["updated_fields"]
    mock_version.update.assert_called_once_with(name="JRV-25.37-7-renamed")


@patch("routes.teams.jira")
def test_update_version_archived(mock_jira, client, mock_version):
    """Test archiving a version."""
    mock_jira.version.return_value = mock_version

    response = client.put("/versions/110436?archived=true")

    assert response.status_code == 200
    assert "archived" in response.json()["updated_fields"]
    mock_version.update.assert_called_once_with(archived=True)
