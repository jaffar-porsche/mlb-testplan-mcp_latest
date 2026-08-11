"""Tests for route module registration."""

import pytest


def test_routes_module_imports():
    """Test all route modules can be imported."""
    from routes import register_routes
    from routes.issues import router as issues_router
    from routes.attachments import router as attachments_router
    from routes.comments import router as comments_router
    from routes.projects import router as projects_router
    from routes.sprints import router as sprints_router
    from routes.links import router as links_router
    from routes.teams import router as teams_router

    assert callable(register_routes)
    assert issues_router is not None
    assert attachments_router is not None
    assert comments_router is not None
    assert projects_router is not None
    assert sprints_router is not None
    assert links_router is not None
    assert teams_router is not None


def test_issues_router_has_routes():
    """Test issues router has expected routes."""
    from routes.issues import router

    paths = [route.path for route in router.routes]

    assert "/issue/{issue_key}" in paths
    assert "/search_issues" in paths


def test_attachments_router_has_routes():
    """Test attachments router has expected routes."""
    from routes.attachments import router

    paths = [route.path for route in router.routes]

    assert "/issue/{issue_key}/attachments" in paths


def test_links_router_has_routes():
    """Test links router has expected routes."""
    from routes.links import router

    paths = [route.path for route in router.routes]

    assert "/link_types" in paths
    assert "/issue/{issue_key}/link" in paths


def test_sprints_router_has_routes():
    """Test sprints router has expected routes."""
    from routes.sprints import router

    paths = [route.path for route in router.routes]

    assert "/sprint/{sprint_id}" in paths
    assert "/sprint/{sprint_id}/issue" in paths


def test_comments_router_has_routes():
    """Test comments router has expected routes."""
    from routes.comments import router

    paths = [route.path for route in router.routes]
    methods = {route.path: route.methods for route in router.routes}

    assert "/issue/{issue_key}/comments" in paths
    assert "/issue/{issue_key}/comments/{comment_id}" in paths
    assert "DELETE" in methods["/issue/{issue_key}/comments/{comment_id}"]


def test_projects_router_has_routes():
    """Test projects router has expected routes."""
    from routes.projects import router

    paths = [route.path for route in router.routes]

    assert "/projects" in paths
    assert "/board/{board_id}/sprints" in paths


def test_teams_router_has_routes():
    """Test teams router has expected routes."""
    from routes.teams import router

    paths = [route.path for route in router.routes]

    assert "/teams" in paths
    assert "/team/features" in paths
    assert "/fields" in paths
    assert "/versions" in paths
    assert "/versions/{version_id}/summary" in paths
    assert "/versions/{version_id}" in paths


def test_users_router_has_routes():
    """Test users router has expected routes."""
    from routes.users import router

    paths = [route.path for route in router.routes]

    assert "/users/search" in paths


def test_routes_module_imports_users():
    """Test users router is registered via register_routes."""
    from routes import users_router

    assert users_router is not None
