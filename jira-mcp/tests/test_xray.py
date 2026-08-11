"""Tests for xRay route behavior."""

from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    """Create a test client with mocked Jira/xRay dependencies."""
    from mcp_server import app

    return TestClient(app)


def test_xray_router_has_test_steps_route():
    """Test xRay router exposes the test steps endpoint."""
    from routes.xray import router

    paths = [route.path for route in router.routes]

    assert "/xray/test/{test_key}/steps" in paths


@patch("routes.xray_tests._proxy_response")
@patch("routes.xray_tests._raise_for_xray")
@patch("routes.xray_tests._request_xray")
def test_get_test_steps_without_version(mock_request_xray, mock_raise_for_xray, mock_proxy_response, client):
    """Test reading test steps without sending a testVersion query parameter."""
    mock_response = MagicMock()
    mock_request_xray.return_value = mock_response
    mock_proxy_response.return_value = {"steps": []}

    response = client.get("/xray/test/OTA-6013/steps")

    assert response.status_code == 200
    assert response.json() == {"steps": []}
    mock_request_xray.assert_called_once_with(
        "GET",
        "https://test.jira.local/rest/raven/2.0/api/test/OTA-6013/steps",
        params=None,
    )
    mock_raise_for_xray.assert_called_once_with(mock_response, "GET test steps OTA-6013")
    mock_proxy_response.assert_called_once_with(mock_response)


@patch("routes.xray_tests._proxy_response")
@patch("routes.xray_tests._raise_for_xray")
@patch("routes.xray_tests._request_xray")
def test_get_test_steps_with_version(mock_request_xray, mock_raise_for_xray, mock_proxy_response, client):
    """Test reading test steps with an explicit testVersion query parameter."""
    mock_response = MagicMock()
    mock_request_xray.return_value = mock_response
    mock_proxy_response.return_value = {"steps": []}

    response = client.get("/xray/test/OTA-6013/steps?testVersion=v1")

    assert response.status_code == 200
    assert response.json() == {"steps": []}
    mock_request_xray.assert_called_once_with(
        "GET",
        "https://test.jira.local/rest/raven/2.0/api/test/OTA-6013/steps",
        params={"testVersion": "v1"},
    )
    mock_raise_for_xray.assert_called_once_with(mock_response, "GET test steps OTA-6013")
    mock_proxy_response.assert_called_once_with(mock_response)


def test_xray_router_has_testset_routes():
    """Test xRay test set endpoints are exposed by the router."""
    from routes.xray_testset import router

    paths = [route.path for route in router.routes]

    assert "/xray/testset/{set_key}/tests" in paths
    assert "/xray/testset/{set_key}/tests/{test_key}" in paths


@patch("routes.xray_testset._proxy_response")
@patch("routes.xray_testset._raise_for_xray")
@patch("routes.xray_testset._request_xray")
def test_add_test_set_tests(mock_request_xray, mock_raise_for_xray, mock_proxy_response, client):
    """Test adding tests to a test set forwards request to xRay with expected payload."""
    mock_response = MagicMock()
    mock_request_xray.return_value = mock_response
    mock_proxy_response.return_value = {"success": True}

    response = client.post("/xray/testset/OTA-6028/tests", json={"keys": ["OTA-6001", "OTA-6002"]})

    assert response.status_code == 200
    assert response.json() == {"success": True}
    mock_request_xray.assert_called_once_with(
        "POST",
        "https://test.jira.local/rest/raven/2.0/api/testset/OTA-6028/test",
        json=["OTA-6001", "OTA-6002"],
    )
    mock_raise_for_xray.assert_called_once_with(mock_response, "POST test set tests OTA-6028")
    mock_proxy_response.assert_called_once_with(mock_response)


@patch("routes.xray_testset._proxy_response")
@patch("routes.xray_testset._raise_for_xray")
@patch("routes.xray_testset._request_xray")
def test_remove_test_set_test(mock_request_xray, mock_raise_for_xray, mock_proxy_response, client):
    """Test removing a test from a test set forwards request to xRay with expected URL."""
    mock_response = MagicMock()
    mock_request_xray.return_value = mock_response
    mock_proxy_response.return_value = {}

    response = client.delete("/xray/testset/OTA-6028/tests/OTA-6001")

    assert response.status_code == 200
    assert response.json() == {}
    mock_request_xray.assert_called_once_with(
        "DELETE",
        "https://test.jira.local/rest/raven/2.0/api/testset/OTA-6028/test/OTA-6001",
    )
    mock_raise_for_xray.assert_called_once_with(mock_response, "DELETE test set test OTA-6028/OTA-6001")
    mock_proxy_response.assert_called_once_with(mock_response)