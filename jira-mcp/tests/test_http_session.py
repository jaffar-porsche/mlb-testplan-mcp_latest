"""Tests for shared HTTP session (client.http_session) and cert propagation.

Verifies that:
1. http_session is created with correct auth config (cert vs proxy)
2. All route modules use http_session instead of bare requests calls
3. Route handlers pass requests through the session (integration-style)
"""

import ast
import os
import pytest
from unittest.mock import patch, MagicMock


# ---------------------------------------------------------------------------
# 1. http_session factory unit tests
# ---------------------------------------------------------------------------


class TestCreateHttpSession:
    """Test _create_http_session produces correctly configured sessions."""

    def test_session_with_cert_tuple(self):
        """Session should have .cert set when cert_tuple is provided."""
        from client import _create_http_session

        session = _create_http_session(cert_tuple=("/tmp/cert.crt", "/tmp/key.key"))

        assert session.cert == ("/tmp/cert.crt", "/tmp/key.key")
        assert "Authorization" in session.headers
        assert session.headers["Authorization"] == "Bearer test-token"
        assert session.headers["Content-Type"] == "application/json"

    def test_session_without_cert_uses_proxy(self):
        """Session without cert should use proxy config (if set)."""
        from client import _create_http_session

        session = _create_http_session(cert_tuple=None)

        assert session.cert is None
        assert "Authorization" in session.headers
        assert session.headers["Authorization"] == "Bearer test-token"

    def test_session_has_bearer_token(self):
        """Session should always carry the PAT as Bearer token."""
        from client import _create_http_session

        session = _create_http_session()

        assert "Bearer test-token" in session.headers.get("Authorization", "")

    def test_session_has_json_content_type(self):
        """Session should default to application/json content type."""
        from client import _create_http_session

        session = _create_http_session()

        assert session.headers["Content-Type"] == "application/json"


class TestHttpSessionProxy:
    """Test that the http_session proxy delegates correctly."""

    def test_http_session_is_importable(self):
        """http_session should be importable from client module."""
        from client import http_session

        assert http_session is not None

    @patch("client._http_session")
    def test_proxy_delegates_get(self, mock_session):
        """_HttpSessionProxy.get should delegate to the real session."""
        from client import _HttpSessionProxy

        proxy = _HttpSessionProxy()
        # The proxy calls get_http_session() which returns _http_session
        # We need to patch at a higher level
        with patch("client.get_http_session") as mock_getter:
            mock_real_session = MagicMock()
            mock_getter.return_value = mock_real_session

            proxy.get("https://example.com")
            mock_real_session.get.assert_called_once_with("https://example.com")


# ---------------------------------------------------------------------------
# 2. Static analysis: no bare requests.get/post/delete in route files
# ---------------------------------------------------------------------------


class TestNoBareRequestsCalls:
    """Verify that route/util modules don't use bare requests.get/post/delete.

    This is a static check that parses the AST of each file and ensures
    no calls like ``requests.get(...)`` exist — only ``http_session.get(...)``
    or ``_sd_get(...)`` patterns should be used.

    The one exception is ``requests.RequestException`` which is a class
    reference (for except clauses), not an HTTP call.
    """

    # Files that previously had bare requests calls
    CHECKED_FILES = [
        "routes/sprints.py",
        "routes/links.py",
        "routes/attachments.py",
        "routes/projects.py",
        "routes/teams.py",
        "utils/agile_hive.py",
    ]

    # Methods that indicate an actual HTTP call (not exception classes)
    BANNED_METHODS = {"get", "post", "put", "delete", "patch", "head", "options"}

    def _find_bare_requests_calls(self, filepath: str) -> list[str]:
        """Parse a Python file and find any ``requests.<method>(...)`` calls."""
        with open(filepath) as f:
            tree = ast.parse(f.read(), filename=filepath)

        violations = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                func = node.func
                # Match: requests.get(...), requests.post(...), etc.
                if (
                    isinstance(func, ast.Attribute)
                    and isinstance(func.value, ast.Name)
                    and func.value.id == "requests"
                    and func.attr in self.BANNED_METHODS
                ):
                    violations.append(f"  line {node.lineno}: requests.{func.attr}()")
        return violations

    @pytest.mark.parametrize("relpath", CHECKED_FILES)
    def test_no_bare_requests_calls(self, relpath):
        """File should not contain bare requests.get/post/delete calls."""
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        filepath = os.path.join(base, relpath)

        violations = self._find_bare_requests_calls(filepath)
        assert not violations, (
            f"{relpath} still has bare requests calls:\n"
            + "\n".join(violations)
            + "\n\nUse http_session from client.py instead."
        )

    def test_servicedesk_uses_http_session_in_helper(self):
        """servicedesk.py should use http_session inside _sd_get."""
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        filepath = os.path.join(base, "routes/servicedesk.py")

        # _sd_get should call http_session.get, not requests.get
        violations = self._find_bare_requests_calls(filepath)
        assert not violations, (
            f"routes/servicedesk.py still has bare requests calls:\n"
            + "\n".join(violations)
        )


# ---------------------------------------------------------------------------
# 3. Route integration tests: verify http_session is used for HTTP calls
# ---------------------------------------------------------------------------


@pytest.fixture
def client():
    """Create a test client with mocked jira client."""
    from mcp_server import app
    from fastapi.testclient import TestClient

    return TestClient(app)


class TestSprintRoutes:
    """Test sprint routes use http_session for HTTP calls."""

    @patch("routes.sprints.http_session")
    def test_get_sprint_uses_session(self, mock_session, client):
        """GET /sprint/{id} should call http_session.get."""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "id": 42,
            "name": "Sprint 1",
            "state": "active",
        }
        mock_session.get.return_value = mock_resp

        response = client.get("/sprint/42")

        assert response.status_code == 200
        mock_session.get.assert_called_once()
        call_url = mock_session.get.call_args[0][0]
        assert "/sprint/42" in call_url

    @patch("routes.sprints.http_session")
    def test_move_issues_to_sprint_uses_session(self, mock_session, client):
        """POST /sprint/{id}/issue should call http_session.post."""
        mock_resp = MagicMock()
        mock_resp.status_code = 204
        mock_session.post.return_value = mock_resp

        response = client.post(
            "/sprint/42/issue",
            json={"issue_keys": ["PROJ-1", "PROJ-2"]},
        )

        assert response.status_code == 200
        mock_session.post.assert_called_once()
        call_url = mock_session.post.call_args[0][0]
        assert "/sprint/42/issue" in call_url

    @patch("routes.sprints.http_session")
    def test_remove_issues_from_sprint_uses_session(self, mock_session, client):
        """DELETE /sprint/{id}/issue should call http_session.post (backlog)."""
        mock_resp = MagicMock()
        mock_resp.status_code = 204
        mock_session.post.return_value = mock_resp

        response = client.request(
            "DELETE",
            "/sprint/42/issue",
            json={"issue_keys": ["PROJ-1"]},
        )

        assert response.status_code == 200
        mock_session.post.assert_called_once()
        call_url = mock_session.post.call_args[0][0]
        assert "/backlog/issue" in call_url

    @patch("routes.sprints.http_session")
    def test_get_sprint_404(self, mock_session, client):
        """GET /sprint/{id} should return 404 when sprint not found."""
        mock_resp = MagicMock()
        mock_resp.status_code = 404
        mock_session.get.return_value = mock_resp

        response = client.get("/sprint/99999")

        assert response.status_code == 404


class TestLinkRoutes:
    """Test link routes use http_session for HTTP calls."""

    @patch("routes.links.http_session")
    def test_delete_link_uses_session(self, mock_session, client):
        """DELETE /issue/{key}/link/{id} should call http_session.delete."""
        mock_resp = MagicMock()
        mock_resp.status_code = 204
        mock_session.delete.return_value = mock_resp

        response = client.delete("/issue/PROJ-1/link/12345")

        assert response.status_code == 200
        mock_session.delete.assert_called_once()
        call_url = mock_session.delete.call_args[0][0]
        assert "/issueLink/12345" in call_url

    @patch("routes.links.http_session")
    def test_delete_link_404(self, mock_session, client):
        """DELETE /issue/{key}/link/{id} should return 404 when not found."""
        mock_resp = MagicMock()
        mock_resp.status_code = 404
        mock_session.delete.return_value = mock_resp

        response = client.delete("/issue/PROJ-1/link/99999")

        assert response.status_code == 404


class TestAttachmentRoutes:
    """Test attachment download uses http_session."""

    @patch("routes.attachments.http_session")
    @patch("routes.attachments.jira")
    def test_download_attachment_uses_session(self, mock_jira, mock_session, client):
        """GET /issue/{key}/attachments/{id}/download should use http_session.get."""
        # Mock issue with attachment
        mock_attachment = MagicMock()
        mock_attachment.id = "10001"
        mock_attachment.filename = "test.txt"
        mock_attachment.mimeType = "text/plain"
        mock_attachment.size = "100"
        mock_attachment.content = "https://jira.local/attachment/10001/test.txt"

        mock_issue = MagicMock()
        mock_issue.fields.attachment = [mock_attachment]
        mock_jira.issue.return_value = mock_issue

        # Mock session response
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.content = b"file content here"
        mock_resp.raise_for_status = MagicMock()
        mock_session.get.return_value = mock_resp

        response = client.get("/issue/PROJ-1/attachments/10001/download")

        assert response.status_code == 200
        mock_session.get.assert_called_once()
        call_url = mock_session.get.call_args[0][0]
        assert "attachment/10001" in call_url


class TestProjectRoutes:
    """Test board sprints route uses http_session."""

    def test_get_board_sprints_uses_session(self, client):
        """GET /board/{id}/sprints should use http_session.get.

        projects.py imports http_session inside the function body, so we
        patch at the client module level via get_http_session.
        """
        mock_session = MagicMock()
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "values": [
                {"id": 1, "name": "Sprint 1", "state": "active"},
            ]
        }
        mock_session.get.return_value = mock_resp

        with patch("client.get_http_session", return_value=mock_session):
            response = client.get("/board/100/sprints")

        assert response.status_code == 200
        mock_session.get.assert_called_once()
        call_url = mock_session.get.call_args[0][0]
        assert "/board/100/sprint" in call_url


class TestAgileHiveUtils:
    """Test agile_hive utility functions use http_session."""

    @patch("utils.agile_hive.http_session")
    def test_resolve_team_name_via_api_uses_session(self, mock_session):
        """resolve_team_name_via_api should use http_session.get."""
        from utils.agile_hive import (
            resolve_team_name_via_api,
            reset_cache,
            _team_name_cache,
        )

        # Clear any cached values
        _team_name_cache.pop("77777", None)

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"title": "DSW - Test Team"}
        mock_session.get.return_value = mock_resp

        name = resolve_team_name_via_api(
            "77777", "https://jira.local", "test-token", None
        )

        assert name == "DSW - Test Team"
        mock_session.get.assert_called_once()
        call_url = mock_session.get.call_args[0][0]
        assert "/rest/teams-api/1.0/team/77777" in call_url

    @patch("utils.agile_hive.http_session")
    def test_resolve_team_name_returns_cached(self, mock_session):
        """resolve_team_name_via_api should return cached name without HTTP call."""
        from utils.agile_hive import resolve_team_name_via_api, _register_team_name

        _register_team_name("66666", "Cached Team")

        name = resolve_team_name_via_api(
            "66666", "https://jira.local", "test-token", None
        )

        assert name == "Cached Team"
        mock_session.get.assert_not_called()

    @patch("utils.agile_hive.http_session")
    def test_resolve_teams_via_issue_properties_uses_session(self, mock_session):
        """_resolve_teams_via_issue_properties should use http_session.get."""
        from utils.agile_hive import (
            _resolve_teams_via_issue_properties,
            _team_name_cache,
        )

        # Clear cached value
        _team_name_cache.pop("55555", None)

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "value": {
                "planningIntervalSprintInfoByPiId": {
                    "100": {"team": "DSW - Property Team"}
                }
            }
        }
        mock_session.get.return_value = mock_resp

        _resolve_teams_via_issue_properties(
            issue_keys=["PROJ-1"],
            teams_involved_ids={"PROJ-1": ["55555"]},
            base_url="https://jira.local",
            pat="test-token",
            proxies=None,
        )

        mock_session.get.assert_called_once()
        call_url = mock_session.get.call_args[0][0]
        assert "/properties/AgileHiveProgramBoard" in call_url

        # Verify the name was cached
        from utils.agile_hive import _lookup_team_name

        assert _lookup_team_name("55555") == "DSW - Property Team"
