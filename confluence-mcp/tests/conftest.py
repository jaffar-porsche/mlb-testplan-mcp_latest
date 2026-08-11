"""Pytest fixtures and configuration for Confluence MCP tests."""
import os
import sys
from unittest.mock import MagicMock, patch

import pytest

# Set required env vars before any imports
os.environ["CONFLUENCE_PAT"] = "test-token"
os.environ["CONFLUENCE_BASE_URL"] = "https://test.confluence.local"
os.environ["HTTP_PROXY"] = ""
os.environ["HTTPS_PROXY"] = ""


def create_mock_confluence():
    """Create a mock Confluence client with pre-configured responses."""
    mock = MagicMock()

    # Mock get_page_by_id
    mock.get_page_by_id.return_value = {
        "id": "12345",
        "title": "Test Page",
        "space": {"key": "TEST"},
        "version": {"number": 1},
        "body": {"storage": {"value": "<p>Test content</p>"}},
        "ancestors": [
            {"id": "11111", "title": "Parent Page"},
            {"id": "10000", "title": "Root Page"}
        ]
    }

    # Mock get_all_pages_from_space
    mock.get_all_pages_from_space.return_value = [
        {"id": "12345", "title": "Test Page 1"},
        {"id": "12346", "title": "Test Page 2"},
        {"id": "12347", "title": "Another Page"}
    ]

    # Mock get_all_spaces
    mock.get_all_spaces.return_value = {
        "results": [
            {"key": "TEST", "name": "Test Space", "type": "global"},
            {"key": "DEV", "name": "Development", "type": "global"}
        ],
        "size": 2
    }

    # Mock get_space
    mock.get_space.return_value = {"key": "TEST", "name": "Test Space"}

    # Mock create_page
    mock.create_page.return_value = {
        "id": "99999",
        "title": "New Page",
        "space": {"key": "TEST"}
    }

    # Mock get_current_user
    mock.get_current_user.return_value = {
        "displayName": "Test User",
        "username": "testuser"
    }

    # Mock CQL search
    mock.cql.return_value = {
        "results": [
            {
                "content": {
                    "id": "12345",
                    "title": "Search Result",
                    "type": "page",
                    "space": {"key": "TEST"}
                }
            }
        ],
        "size": 1
    }

    # Mock _session for raw API calls (used by get_child_pages, etc.)
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "results": [
            {
                "id": "22222",
                "title": "Child Page 1",
                "space": {"key": "TEST"},
                "version": {"number": 1}
            },
            {
                "id": "22223",
                "title": "Child Page 2",
                "space": {"key": "TEST"},
                "version": {"number": 3}
            }
        ],
        "size": 2,
        "_links": {}
    }
    mock._session.get.return_value = mock_response
    mock._session.post.return_value = mock_response
    mock._session.put.return_value = mock_response
    mock._session.delete.return_value = MagicMock(status_code=204)

    # Set URL for building API paths
    mock.url = "https://test.confluence.local"

    return mock


# Create and patch the mock before importing the app
_mock_confluence = create_mock_confluence()

# Mock the atlassian module
_mock_atlassian = MagicMock()
_mock_atlassian.Confluence.return_value = _mock_confluence
sys.modules["atlassian"] = _mock_atlassian


@pytest.fixture
def mock_confluence():
    """Provide access to the mock Confluence client."""
    return _mock_confluence


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    from fastapi.testclient import TestClient
    from mcp_server import app

    return TestClient(app)


@pytest.fixture
def reset_mocks():
    """Reset all mock call counts between tests."""
    _mock_confluence.reset_mock()
    yield
    _mock_confluence.reset_mock()
