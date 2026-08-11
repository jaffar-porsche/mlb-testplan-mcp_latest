"""Tests for Confluence user search endpoint."""
from unittest.mock import MagicMock


class TestUserSearch:
    """Tests for user search endpoint."""

    def _make_user_search_response(self, users, status_code=200):
        """Helper to create a mock user search API response."""
        resp = MagicMock()
        resp.status_code = status_code
        resp.json.return_value = {
            "results": [
                {
                    "user": {
                        "username": u["username"],
                        "displayName": u["displayName"],
                        "userKey": u.get("userKey", u["username"]),
                        "type": "known",
                    }
                }
                for u in users
            ],
            "size": len(users),
        }
        return resp

    def test_search_users(self, client, mock_confluence):
        """Test searching users by name."""
        mock_confluence._session.get.return_value = self._make_user_search_response([
            {"username": "tjrpp43", "displayName": "Manke, Sandro (FDC2_EXTERN)"},
        ])

        response = client.get("/users/search?query=sandro")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["users"][0]["username"] == "tjrpp43"
        assert data["users"][0]["displayName"] == "Manke, Sandro (FDC2_EXTERN)"

        mock_confluence._session.get.side_effect = None

    def test_search_users_empty_results(self, client, mock_confluence):
        """Test searching users with no matches."""
        mock_confluence._session.get.return_value = self._make_user_search_response([])

        response = client.get("/users/search?query=nonexistent")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert data["users"] == []

        mock_confluence._session.get.side_effect = None

    def test_search_users_multiple_results(self, client, mock_confluence):
        """Test multiple users returned."""
        mock_confluence._session.get.return_value = self._make_user_search_response([
            {"username": "user1", "displayName": "Alice Smith"},
            {"username": "user2", "displayName": "Bob Smith"},
        ])

        response = client.get("/users/search?query=smith")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        assert data["users"][0]["username"] == "user1"
        assert data["users"][1]["username"] == "user2"

        mock_confluence._session.get.side_effect = None

    def test_search_users_custom_max_results(self, client, mock_confluence):
        """Test custom max_results parameter is forwarded to API."""
        mock_confluence._session.get.return_value = self._make_user_search_response([])

        response = client.get("/users/search?query=test&max_results=25")
        assert response.status_code == 200

        call_args = mock_confluence._session.get.call_args
        assert call_args[1]["params"]["limit"] == 25

        mock_confluence._session.get.side_effect = None

    def test_search_uses_cql_with_type_user(self, client, mock_confluence):
        """Test that CQL query uses type='user' and user.fullname."""
        mock_confluence._session.get.return_value = self._make_user_search_response([])

        response = client.get("/users/search?query=sandro")
        assert response.status_code == 200

        call_args = mock_confluence._session.get.call_args
        cql = call_args[1]["params"]["cql"]
        assert 'type = "user"' in cql
        assert 'user.fullname ~ "sandro"' in cql

        mock_confluence._session.get.side_effect = None

    def test_search_uses_standard_search_endpoint(self, client, mock_confluence):
        """Test that the standard /rest/api/search endpoint is used."""
        mock_confluence._session.get.return_value = self._make_user_search_response([])

        response = client.get("/users/search?query=test")
        assert response.status_code == 200

        call_args = mock_confluence._session.get.call_args
        url = call_args[0][0]
        assert url.endswith("/rest/api/search")

        mock_confluence._session.get.side_effect = None

    def test_search_sanitizes_quotes_in_query(self, client, mock_confluence):
        """Test that double quotes in query are escaped to prevent CQL injection."""
        mock_confluence._session.get.return_value = self._make_user_search_response([])

        response = client.get('/users/search?query=test"injection')
        assert response.status_code == 200

        call_args = mock_confluence._session.get.call_args
        cql = call_args[1]["params"]["cql"]
        assert 'test\\"injection' in cql

        mock_confluence._session.get.side_effect = None

    def test_search_users_fallback_on_api_error(self, client, mock_confluence):
        """Test fallback to username lookup when CQL search fails."""
        error_resp = MagicMock()
        error_resp.status_code = 400

        mock_confluence._session.get.return_value = error_resp
        mock_confluence.get_user_details_by_username.return_value = {
            "username": "sandro",
            "displayName": "Sandro Manke",
            "userKey": "sandro",
            "type": "known",
        }

        response = client.get("/users/search?query=sandro")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["users"][0]["username"] == "sandro"

        mock_confluence.get_user_details_by_username.assert_called_once_with("sandro")

        mock_confluence._session.get.side_effect = None
        mock_confluence.get_user_details_by_username.side_effect = None

    def test_search_users_fallback_no_match(self, client, mock_confluence):
        """Test fallback returns empty when username lookup also fails."""
        error_resp = MagicMock()
        error_resp.status_code = 400

        mock_confluence._session.get.return_value = error_resp
        mock_confluence.get_user_details_by_username.side_effect = Exception("Not found")

        response = client.get("/users/search?query=nonexistent")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert data["users"] == []

        mock_confluence._session.get.side_effect = None
        mock_confluence.get_user_details_by_username.side_effect = None

    def test_search_users_response_format(self, client, mock_confluence):
        """Test response includes all expected user fields."""
        mock_confluence._session.get.return_value = self._make_user_search_response([
            {"username": "abc123", "displayName": "Test User", "userKey": "abc123"},
        ])

        response = client.get("/users/search?query=test")
        assert response.status_code == 200
        data = response.json()

        user = data["users"][0]
        assert "username" in user
        assert "displayName" in user
        assert "userKey" in user
        assert "type" in user

        mock_confluence._session.get.side_effect = None


class TestUserRouterRegistration:
    """Tests for users router registration."""

    def test_users_router_has_routes(self):
        """Test users router has expected routes."""
        from routes.users import router

        paths = [route.path for route in router.routes]
        assert "/users/search" in paths

    def test_routes_module_imports_users(self):
        """Test users router is registered via register_routes."""
        from routes import users_router

        assert users_router is not None
