"""Tests for user search endpoint."""
import pytest
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient


@pytest.fixture
def client():
    """Create a test client with mocked jira client."""
    from mcp_server import app
    return TestClient(app)


@pytest.fixture
def mock_user():
    """Create a mock Jira user object."""
    user = MagicMock()
    user.name = "tjrpp43"
    user.key = "tjrpp43"
    user.displayName = "Manke, Sandro (FDC2_EXTERN)"
    user.emailAddress = "net.sandro.manke@mhp.com"
    user.active = True
    return user


def test_format_user():
    """Test _format_user extracts correct fields from user object."""
    from routes.users import _format_user

    user = MagicMock()
    user.name = "abc123"
    user.displayName = "Test User"
    user.emailAddress = "test@example.com"
    user.active = True

    result = _format_user(user)

    assert result["username"] == "abc123"
    assert result["displayName"] == "Test User"
    assert result["emailAddress"] == "test@example.com"
    assert result["active"] is True


def test_format_user_fallback_to_key():
    """Test _format_user falls back to key when name is None."""
    from routes.users import _format_user

    user = MagicMock()
    user.name = None
    user.key = "fallback_key"
    user.displayName = "Fallback User"
    user.emailAddress = None
    user.active = False

    result = _format_user(user)

    assert result["username"] == "fallback_key"


@patch("routes.users.jira")
def test_search_users_global(mock_jira, client, mock_user):
    """Test searching users without project scope."""
    mock_jira.search_users.return_value = [mock_user]

    response = client.get("/users/search?query=sandro")

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["users"][0]["username"] == "tjrpp43"
    assert data["users"][0]["displayName"] == "Manke, Sandro (FDC2_EXTERN)"

    mock_jira.search_users.assert_called_once_with(
        user="sandro", maxResults=10
    )


@patch("routes.users.jira")
def test_search_users_with_project_scope(mock_jira, client, mock_user):
    """Test searching users scoped to a project."""
    mock_jira.search_assignable_users_for_issues.return_value = [mock_user]

    response = client.get(
        "/users/search?query=sandro&project_key=DSWTEAMSYS"
    )

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["users"][0]["emailAddress"] == "net.sandro.manke@mhp.com"

    mock_jira.search_assignable_users_for_issues.assert_called_once_with(
        username="sandro", project="DSWTEAMSYS", maxResults=10
    )


@patch("routes.users.jira")
def test_search_users_empty_results(mock_jira, client):
    """Test searching users with no matches."""
    mock_jira.search_users.return_value = []

    response = client.get("/users/search?query=nonexistent")

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 0
    assert data["users"] == []


@patch("routes.users.jira")
def test_search_users_custom_max_results(mock_jira, client):
    """Test max_results parameter is passed through."""
    mock_jira.search_users.return_value = []

    response = client.get("/users/search?query=test&max_results=25")

    assert response.status_code == 200
    mock_jira.search_users.assert_called_once_with(
        user="test", maxResults=25
    )


@patch("routes.users.jira")
def test_search_users_jira_error(mock_jira, client):
    """Test error handling when Jira API fails."""
    mock_jira.search_users.side_effect = Exception("Jira connection failed")

    response = client.get("/users/search?query=test")

    assert response.status_code == 500
    assert "Failed to search users" in response.json()["detail"]


@patch("routes.users.jira")
def test_search_users_multiple_results(mock_jira, client):
    """Test multiple users returned."""
    users = []
    for i, (name, display) in enumerate([
        ("user1", "Alice Smith"),
        ("user2", "Bob Smith"),
    ]):
        u = MagicMock()
        u.name = name
        u.displayName = display
        u.emailAddress = f"{name}@example.com"
        u.active = True
        users.append(u)

    mock_jira.search_users.return_value = users

    response = client.get("/users/search?query=smith")

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    assert data["users"][0]["username"] == "user1"
    assert data["users"][1]["username"] == "user2"
