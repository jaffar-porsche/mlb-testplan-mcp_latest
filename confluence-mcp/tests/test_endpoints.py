"""Tests for Confluence MCP endpoints."""
from unittest.mock import MagicMock, call

import pytest


class TestHealthEndpoints:
    """Tests for health check endpoints."""

    def test_health_check(self, client):
        """Test health check returns healthy status."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "Confluence MCP Server"

    def test_test_connection(self, client):
        """Test connection endpoint returns user info."""
        response = client.get("/test_connection")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "connected"
        assert "user" in data


class TestPageEndpoints:
    """Tests for page-related endpoints."""

    def test_get_page(self, client, mock_confluence):
        """Test getting a page by ID."""
        response = client.get("/page/12345")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "12345"
        assert data["title"] == "Test Page"
        assert data["space"] == "TEST"
        assert "body" in data
        assert "url" in data

    def test_get_page_calls_api_with_expand(self, client, mock_confluence):
        """Test that get_page requests correct expansions."""
        client.get("/page/12345")
        mock_confluence.get_page_by_id.assert_called_with(
            "12345",
            expand="body.storage,space,version"
        )

    def test_create_page(self, client, mock_confluence):
        """Test creating a new page."""
        response = client.post("/create_page", json={
            "space_key": "TEST",
            "title": "New Page",
            "body": "<p>Content</p>"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "99999"
        assert data["title"] == "New Page"

    def test_create_page_simple(self, client, mock_confluence):
        """Test creating a page via simplified endpoint."""
        response = client.post("/create_page_simple", json={
            "space_key": "TEST",
            "title": "Simple Page",
            "body": "<p>Simple content</p>"
        })
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert data["method"] == "simplified"


class TestHierarchyEndpoints:
    """Tests for page hierarchy traversal endpoints."""

    def test_get_child_pages(self, client, mock_confluence):
        """Test getting child pages of a parent page."""
        response = client.get("/page/12345/children")
        assert response.status_code == 200
        data = response.json()
        assert data["parent_id"] == "12345"
        assert "children" in data
        assert len(data["children"]) == 2
        assert data["children"][0]["id"] == "22222"
        assert data["children"][0]["title"] == "Child Page 1"
        assert "total" in data

    def test_get_child_pages_with_limit(self, client, mock_confluence):
        """Test getting child pages with custom limit."""
        response = client.get("/page/12345/children?limit=5")
        assert response.status_code == 200
        # Verify the API was called with limit param
        mock_confluence._session.get.assert_called()
        call_args = mock_confluence._session.get.call_args
        assert call_args[1]["params"]["limit"] == 5

    def test_get_child_pages_returns_url(self, client, mock_confluence):
        """Test that child pages include URL."""
        response = client.get("/page/12345/children")
        data = response.json()
        for child in data["children"]:
            assert "url" in child
            assert child["id"] in child["url"]

    def test_get_page_ancestors(self, client, mock_confluence):
        """Test getting ancestor chain of a page."""
        response = client.get("/page/12345/ancestors")
        assert response.status_code == 200
        data = response.json()
        assert data["page_id"] == "12345"
        assert data["page_title"] == "Test Page"
        assert data["space"] == "TEST"
        assert "ancestors" in data
        assert len(data["ancestors"]) == 2
        assert data["depth"] == 2

    def test_get_page_ancestors_order(self, client, mock_confluence):
        """Test ancestors are returned in correct order (root to parent)."""
        response = client.get("/page/12345/ancestors")
        data = response.json()
        # First ancestor should be closer to root
        assert data["ancestors"][0]["title"] == "Parent Page"
        assert data["ancestors"][1]["title"] == "Root Page"

    def test_get_page_ancestors_includes_urls(self, client, mock_confluence):
        """Test that ancestors include URLs."""
        response = client.get("/page/12345/ancestors")
        data = response.json()
        for ancestor in data["ancestors"]:
            assert "url" in ancestor
            assert ancestor["id"] in ancestor["url"]


class TestSearchEndpoints:
    """Tests for search endpoints."""

    def test_search_content(self, client, mock_confluence):
        """Test CQL search."""
        response = client.get("/search?query=test")
        assert response.status_code == 200
        data = response.json()
        assert "results" in data
        assert "total" in data

    def test_search_simple(self, client, mock_confluence):
        """Test simple search within a space."""
        # search_simple now uses _fetch_all_space_pages via _session.get
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "results": [
                {"id": "12345", "title": "Test Page 1"},
                {"id": "12346", "title": "Test Page 2"},
                {"id": "12347", "title": "Another Page"}
            ],
            "size": 3,
            "_links": {}
        }
        mock_confluence._session.get.return_value = mock_resp

        response = client.get("/search_simple?space_key=TEST")
        assert response.status_code == 200
        data = response.json()
        assert "results" in data
        assert len(data["results"]) == 3
        assert data["total"] == 3
        assert "has_more" in data

        mock_confluence._session.get.side_effect = None

    def test_search_simple_with_query(self, client, mock_confluence):
        """Test simple search filters by query."""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "results": [
                {"id": "12345", "title": "Test Page 1"},
                {"id": "12346", "title": "Test Page 2"},
                {"id": "12347", "title": "Another Page"}
            ],
            "size": 3,
            "_links": {}
        }
        mock_confluence._session.get.return_value = mock_resp

        response = client.get("/search_simple?space_key=TEST&query=Test")
        assert response.status_code == 200
        data = response.json()
        # Should filter to pages with "Test" in title
        for result in data["results"]:
            assert "Test" in result["title"]

        mock_confluence._session.get.side_effect = None


class TestSpaceEndpoints:
    """Tests for space-related endpoints."""

    def test_list_spaces(self, client, mock_confluence):
        """Test listing all spaces."""
        response = client.get("/spaces")
        assert response.status_code == 200
        data = response.json()
        assert "spaces" in data
        assert len(data["spaces"]) == 2
        assert data["spaces"][0]["key"] == "TEST"
        assert "total" in data


class TestUpdateEndpoints:
    """Tests for update endpoints."""

    def test_update_page_title(self, client, mock_confluence):
        """Test updating page title."""
        # Configure mock response for update
        mock_response = mock_confluence._session.put.return_value
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": "12345",
            "title": "Updated Title",
            "version": {"number": 2}
        }

        response = client.put("/page/12345", json={
            "title": "Updated Title"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Updated Title"
        assert data["version"] == 2


class TestMoveEndpoint:
    """Tests for the move/reparent page endpoint."""

    def test_move_page_to_new_parent(self, client, mock_confluence):
        """Test moving a page under a new parent."""
        # Mock: source page has parent "11111"
        mock_confluence.get_page_by_id.side_effect = [
            # First call: source page
            {
                "id": "12345",
                "title": "Test Page",
                "space": {"key": "TEST"},
                "version": {"number": 3},
                "body": {"storage": {"value": "<p>Content</p>"}},
                "ancestors": [{"id": "10000", "title": "Root"}, {"id": "11111", "title": "Old Parent"}]
            },
            # Second call: target parent validation
            {
                "id": "55555",
                "title": "New Parent",
                "ancestors": [{"id": "10000", "title": "Root"}]
            }
        ]

        mock_response = mock_confluence._session.put.return_value
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": "12345",
            "title": "Test Page",
            "version": {"number": 4}
        }

        response = client.put("/page/12345/move", json={"parent_id": "55555"})
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "12345"
        assert data["parent_id"] == "55555"
        assert data["previous_parent_id"] == "11111"
        assert data["version"] == 4

        # Verify the PUT payload included the new ancestor
        put_call = mock_confluence._session.put.call_args
        payload = put_call[1]["json"]
        assert payload["ancestors"] == [{"id": "55555"}]
        assert payload["version"]["number"] == 4

        # Reset side_effect for other tests
        mock_confluence.get_page_by_id.side_effect = None
        mock_confluence.get_page_by_id.return_value = {
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

    def test_move_page_to_root(self, client, mock_confluence):
        """Test moving a page to space root (no parent)."""
        mock_confluence.get_page_by_id.return_value = {
            "id": "12345",
            "title": "Test Page",
            "space": {"key": "TEST"},
            "version": {"number": 2},
            "body": {"storage": {"value": "<p>Content</p>"}},
            "ancestors": [{"id": "10000", "title": "Root"}, {"id": "11111", "title": "Parent"}]
        }

        mock_response = mock_confluence._session.put.return_value
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": "12345",
            "title": "Test Page",
            "version": {"number": 3}
        }

        response = client.put("/page/12345/move", json={})
        assert response.status_code == 200
        data = response.json()
        assert data["parent_id"] == "root"

        # Verify empty ancestors in payload
        put_call = mock_confluence._session.put.call_args
        payload = put_call[1]["json"]
        assert payload["ancestors"] == []

    def test_move_page_noop_same_parent(self, client, mock_confluence):
        """Test that moving to current parent returns early without API call."""
        mock_confluence.get_page_by_id.return_value = {
            "id": "12345",
            "title": "Test Page",
            "space": {"key": "TEST"},
            "version": {"number": 2},
            "body": {"storage": {"value": "<p>Content</p>"}},
            "ancestors": [{"id": "10000", "title": "Root"}, {"id": "11111", "title": "Parent"}]
        }

        mock_confluence._session.put.reset_mock()
        response = client.put("/page/12345/move", json={"parent_id": "11111"})
        assert response.status_code == 200
        data = response.json()
        assert "no move needed" in data["message"]

    def test_move_page_prevents_circular(self, client, mock_confluence):
        """Test that moving a page under its own descendant is rejected."""
        mock_confluence.get_page_by_id.side_effect = [
            # Source page
            {
                "id": "12345",
                "title": "Parent Page",
                "space": {"key": "TEST"},
                "version": {"number": 1},
                "body": {"storage": {"value": "<p>Content</p>"}},
                "ancestors": [{"id": "10000", "title": "Root"}]
            },
            # Target parent — is a descendant of source (source 12345 is in its ancestors)
            {
                "id": "99999",
                "title": "Descendant Page",
                "ancestors": [
                    {"id": "10000", "title": "Root"},
                    {"id": "12345", "title": "Parent Page"}
                ]
            }
        ]

        response = client.put("/page/12345/move", json={"parent_id": "99999"})
        assert response.status_code == 400
        assert "descendant" in response.json()["detail"]

        # Reset side_effect
        mock_confluence.get_page_by_id.side_effect = None
        mock_confluence.get_page_by_id.return_value = {
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


class TestSearchCQLEndpoint:
    """Tests for the dedicated search_cql endpoint.

    Covers the issue where passing CQL as query to search_content was
    wrapped in text~, making structural queries impossible. Now a
    separate endpoint handles raw CQL.
    """

    def test_raw_cql_passed_directly(self, client, mock_confluence):
        """Test that cql parameter is passed directly without wrapping."""
        response = client.get("/search_cql?cql=type = page AND space = PCDS")
        assert response.status_code == 200
        mock_confluence.cql.assert_called_with(
            "type = page AND space = PCDS", limit=25
        )

    def test_cql_with_custom_limit(self, client, mock_confluence):
        """Test that limit parameter is forwarded with raw CQL."""
        response = client.get(
            "/search_cql?cql=type = page AND space = TEST&limit=100"
        )
        assert response.status_code == 200
        mock_confluence.cql.assert_called_with(
            "type = page AND space = TEST", limit=100
        )

    def test_cql_ancestor_query(self, client, mock_confluence):
        """Test CQL ancestor query — the original use case that failed."""
        response = client.get(
            "/search_cql?cql=type = page AND ancestor = 27075880"
        )
        assert response.status_code == 200
        mock_confluence.cql.assert_called_with(
            "type = page AND ancestor = 27075880", limit=25
        )

    def test_cql_required(self, client, mock_confluence):
        """Test that cql parameter is required."""
        response = client.get("/search_cql")
        assert response.status_code == 422


class TestSearchContentTextSearch:
    """Tests for search_content text search endpoint.

    Verifies that search_content only does text search (text~),
    and that the query parameter is required.
    """

    def test_text_search_wraps_in_cql(self, client, mock_confluence):
        """Test that query is wrapped in text~ CQL."""
        response = client.get("/search?query=Angular&space_key=PCDS")
        assert response.status_code == 200
        mock_confluence.cql.assert_called_with(
            "space = 'PCDS' AND text ~ 'Angular'", limit=10
        )

    def test_text_search_without_space(self, client, mock_confluence):
        """Test text search without space_key restriction."""
        response = client.get("/search?query=KD-VBV")
        assert response.status_code == 200
        mock_confluence.cql.assert_called_with(
            "text ~ 'KD-VBV'", limit=10
        )

    def test_query_required(self, client, mock_confluence):
        """Test that query parameter is required."""
        response = client.get("/search")
        assert response.status_code == 422


class TestSearchSimplePagination:
    """Tests for search_simple pagination through all space pages.

    Covers the issue where only the first 50 pages were fetched,
    making pages beyond that invisible to search.
    """

    def _make_page_response(self, pages, has_next=False):
        """Helper to create a mock API response."""
        resp = MagicMock()
        resp.status_code = 200
        links = {"next": "/rest/api/content?start=200"} if has_next else {}
        resp.json.return_value = {
            "results": pages,
            "size": len(pages),
            "_links": links
        }
        return resp

    def test_fetches_all_pages_not_just_first_batch(self, client, mock_confluence):
        """Test that search_simple paginates through all pages in a space."""
        # Simulate 2 batches: first returns 200 pages (has_next), second returns 50
        batch1 = [{"id": str(i), "title": f"Page {i}"} for i in range(200)]
        batch2 = [{"id": str(i), "title": f"Page {i}"} for i in range(200, 250)]

        mock_confluence._session.get.side_effect = [
            self._make_page_response(batch1, has_next=True),
            self._make_page_response(batch2, has_next=False),
        ]

        response = client.get("/search_simple?space_key=TEST&limit=200")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 250
        assert data["has_more"] is True  # 250 total, returning 200
        assert len(data["results"]) == 200

        # Reset
        mock_confluence._session.get.side_effect = None

    def test_pagination_start_offset(self, client, mock_confluence):
        """Test that start parameter offsets results correctly."""
        pages = [{"id": str(i), "title": f"Page {i}"} for i in range(10)]
        mock_confluence._session.get.return_value = self._make_page_response(pages)

        response = client.get("/search_simple?space_key=TEST&start=5&limit=3")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 10
        assert data["start"] == 5
        assert data["limit"] == 3
        assert len(data["results"]) == 3
        assert data["results"][0]["id"] == "5"
        assert data["has_more"] is True

        mock_confluence._session.get.side_effect = None

    def test_has_more_false_when_all_returned(self, client, mock_confluence):
        """Test has_more is false when all results fit in the response."""
        pages = [{"id": str(i), "title": f"Page {i}"} for i in range(3)]
        mock_confluence._session.get.return_value = self._make_page_response(pages)

        response = client.get("/search_simple?space_key=TEST&limit=50")
        assert response.status_code == 200
        data = response.json()
        assert data["has_more"] is False
        assert data["total"] == 3

        mock_confluence._session.get.side_effect = None

    def test_limit_capped_at_200(self, client, mock_confluence):
        """Test that limit is capped at 200 even if a higher value is requested."""
        pages = [{"id": str(i), "title": f"Page {i}"} for i in range(5)]
        mock_confluence._session.get.return_value = self._make_page_response(pages)

        response = client.get("/search_simple?space_key=TEST&limit=999")
        assert response.status_code == 200
        data = response.json()
        assert data["limit"] == 200

        mock_confluence._session.get.side_effect = None

    def test_title_filter_case_insensitive(self, client, mock_confluence):
        """Test that query filter is case-insensitive."""
        pages = [
            {"id": "1", "title": "Angular Client Cache"},
            {"id": "2", "title": "Backend Setup"},
            {"id": "3", "title": "angular testing"},
        ]
        mock_confluence._session.get.return_value = self._make_page_response(pages)

        response = client.get("/search_simple?space_key=TEST&query=angular")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        assert all("angular" in r["title"].lower() for r in data["results"])

        mock_confluence._session.get.side_effect = None


class TestListSpacePages:
    """Tests for the list_space_pages endpoint.

    Covers the missing ability to enumerate all pages in a space
    with parent info for orphan detection.
    """

    def _make_page_response(self, pages):
        resp = MagicMock()
        resp.status_code = 200
        resp.json.return_value = {
            "results": pages,
            "size": len(pages),
            "_links": {}
        }
        return resp

    def test_lists_pages_with_parent_id(self, client, mock_confluence):
        """Test that each page includes its parent_id."""
        pages = [
            {"id": "1", "title": "Root", "ancestors": []},
            {"id": "2", "title": "Child", "ancestors": [{"id": "1", "title": "Root"}]},
            {"id": "3", "title": "Grandchild", "ancestors": [
                {"id": "1", "title": "Root"},
                {"id": "2", "title": "Child"}
            ]},
        ]
        mock_confluence._session.get.return_value = self._make_page_response(pages)

        response = client.get("/space/TEST/pages")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 3

        by_id = {p["id"]: p for p in data["pages"]}
        assert by_id["1"]["parent_id"] is None  # root — orphan
        assert by_id["2"]["parent_id"] == "1"
        assert by_id["3"]["parent_id"] == "2"

        mock_confluence._session.get.side_effect = None

    def test_detects_orphan_pages(self, client, mock_confluence):
        """Test that orphan pages (no ancestors) have parent_id=None."""
        pages = [
            {"id": "100", "title": "Space Home", "ancestors": []},
            {"id": "200", "title": "Orphan Page", "ancestors": []},
            {"id": "300", "title": "Nested Page", "ancestors": [
                {"id": "100", "title": "Space Home"}
            ]},
        ]
        mock_confluence._session.get.return_value = self._make_page_response(pages)

        response = client.get("/space/TEST/pages")
        data = response.json()

        orphans = [p for p in data["pages"] if p["parent_id"] is None]
        assert len(orphans) == 2
        orphan_titles = {p["title"] for p in orphans}
        assert "Space Home" in orphan_titles
        assert "Orphan Page" in orphan_titles

        mock_confluence._session.get.side_effect = None

    def test_pagination(self, client, mock_confluence):
        """Test start/limit pagination on list_space_pages."""
        pages = [{"id": str(i), "title": f"Page {i}", "ancestors": []} for i in range(10)]
        mock_confluence._session.get.return_value = self._make_page_response(pages)

        response = client.get("/space/TEST/pages?start=3&limit=4")
        data = response.json()
        assert data["total"] == 10
        assert len(data["pages"]) == 4
        assert data["pages"][0]["id"] == "3"
        assert data["has_more"] is True

        mock_confluence._session.get.side_effect = None


class TestChildPagesPagination:
    """Tests for get_child_pages pagination and fetch_all.

    Covers the issue where get_child_pages returned max 25 results
    with an unreliable has_more field.
    """

    def _make_children_response(self, children, has_next=False):
        resp = MagicMock()
        resp.status_code = 200
        links = {"next": "/rest/api/content/123/child/page?start=200"} if has_next else {}
        resp.json.return_value = {
            "results": [
                {"id": c["id"], "title": c["title"],
                 "space": {"key": "TEST"}, "version": {"number": 1}}
                for c in children
            ],
            "size": len(children),
            "_links": links
        }
        return resp

    def test_has_more_uses_links_not_size(self, client, mock_confluence):
        """Test that has_more is based on _links.next, not the size field."""
        children = [{"id": str(i), "title": f"Child {i}"} for i in range(25)]

        # _links has "next" → there are more pages
        mock_confluence._session.get.return_value = self._make_children_response(
            children, has_next=True
        )

        response = client.get("/page/12345/children?limit=25")
        data = response.json()
        assert data["has_more"] is True

        # Same number of children but no "next" link → no more
        mock_confluence._session.get.return_value = self._make_children_response(
            children, has_next=False
        )

        response = client.get("/page/12345/children?limit=25")
        data = response.json()
        assert data["has_more"] is False

        mock_confluence._session.get.side_effect = None

    def test_start_offset(self, client, mock_confluence):
        """Test that start parameter is passed to the API."""
        children = [{"id": "1", "title": "Child 1"}]
        mock_confluence._session.get.return_value = self._make_children_response(children)

        response = client.get("/page/12345/children?start=50&limit=25")
        assert response.status_code == 200
        data = response.json()
        assert data["start"] == 50
        assert data["limit"] == 25

        # Verify start was sent to the API
        call_args = mock_confluence._session.get.call_args
        assert call_args[1]["params"]["start"] == 50

        mock_confluence._session.get.side_effect = None

    def test_fetch_all_paginates_through_all_children(self, client, mock_confluence):
        """Test that fetch_all=true collects all children across multiple pages."""
        batch1 = [{"id": str(i), "title": f"Child {i}"} for i in range(200)]
        batch2 = [{"id": str(i), "title": f"Child {i}"} for i in range(200, 275)]

        mock_confluence._session.get.side_effect = [
            self._make_children_response(batch1, has_next=True),
            self._make_children_response(batch2, has_next=False),
        ]

        response = client.get("/page/12345/children?fetch_all=true")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 275
        assert len(data["children"]) == 275
        assert data["has_more"] is False

        mock_confluence._session.get.side_effect = None

    def test_limit_capped_at_200(self, client, mock_confluence):
        """Test that limit is capped at 200."""
        children = [{"id": "1", "title": "Child 1"}]
        mock_confluence._session.get.return_value = self._make_children_response(children)

        response = client.get("/page/12345/children?limit=500")
        data = response.json()
        assert data["limit"] == 200

        mock_confluence._session.get.side_effect = None

    def test_response_includes_pagination_fields(self, client, mock_confluence):
        """Test that response always includes start, limit, has_more."""
        children = [{"id": "1", "title": "Child 1"}]
        mock_confluence._session.get.return_value = self._make_children_response(children)

        response = client.get("/page/12345/children")
        data = response.json()
        assert "start" in data
        assert "limit" in data
        assert "has_more" in data

        mock_confluence._session.get.side_effect = None


class TestDeletePageOrphanWarning:
    """Tests for delete_page reparented children warning.

    Covers the issue where deleting a page with cascade=false silently
    reparented child pages to the space root, creating orphans.
    """

    def _setup_delete_mocks(self, mock_confluence, children=None):
        """Configure mocks for delete tests."""
        mock_confluence.get_page_by_id.return_value = {
            "id": "12345",
            "title": "Page To Delete",
            "space": {"key": "TEST"},
            "version": {"number": 1},
        }

        child_results = children or []
        child_resp = MagicMock()
        child_resp.status_code = 200
        child_resp.json.return_value = {"results": child_results}

        delete_resp = MagicMock()
        delete_resp.status_code = 204

        mock_confluence._session.get.return_value = child_resp
        mock_confluence._session.delete.return_value = delete_resp

    def test_delete_warns_about_reparented_children(self, client, mock_confluence):
        """Test that deleting a page with children returns a warning."""
        self._setup_delete_mocks(mock_confluence, children=[
            {"id": "30001", "title": "Child A"},
            {"id": "30002", "title": "Child B"},
            {"id": "30003", "title": "Child C"},
        ])

        response = client.delete("/page/12345")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "warning" in data
        assert "3 child page(s)" in data["warning"]
        assert "cascade=true" in data["warning"]
        assert "reparented_children" in data
        assert len(data["reparented_children"]) == 3
        assert data["reparented_children"][0]["id"] == "30001"

        mock_confluence._session.get.side_effect = None

    def test_delete_no_warning_when_no_children(self, client, mock_confluence):
        """Test that deleting a leaf page has no warning."""
        self._setup_delete_mocks(mock_confluence, children=[])

        response = client.delete("/page/12345")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "warning" not in data
        assert "reparented_children" not in data

        mock_confluence._session.get.side_effect = None

    def test_delete_cascade_no_reparent_warning(self, client, mock_confluence):
        """Test that cascade=true delete doesn't warn about reparenting."""
        children = [
            {"id": "30001", "title": "Child A"},
            {"id": "30002", "title": "Child B"},
        ]
        self._setup_delete_mocks(mock_confluence, children=children)

        # For cascade, _collect_descendants also uses _session.get
        # Mock it to return children on first call (pre-check), then
        # empty on subsequent calls (descendant collection)
        child_resp = MagicMock()
        child_resp.status_code = 200
        child_resp.json.return_value = {"results": children}

        empty_resp = MagicMock()
        empty_resp.status_code = 200
        empty_resp.json.return_value = {"results": []}

        mock_confluence._session.get.side_effect = [
            child_resp,  # _get_direct_children
            child_resp,  # _collect_descendants: first level
            empty_resp,  # _collect_descendants: Child A children
            empty_resp,  # _collect_descendants: Child B children
        ]

        response = client.delete("/page/12345?cascade=true")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["cascade"] is True
        assert "warning" not in data
        assert data["deleted_count"] == 3  # parent + 2 children

        mock_confluence._session.get.side_effect = None
