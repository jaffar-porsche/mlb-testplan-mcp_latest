"""Tests for configuration module."""
import pytest


def test_config_constants():
    """Test that config module defines expected constants."""
    from config import (
        JIRA_BASE_URL,
        MAX_IMAGE_SIZE,
        MAX_TEXT_SIZE,
        MAX_PDF_SIZE,
        IMAGE_TYPES,
        TEXT_TYPES,
        SPRINT_FIELD_ID,
        _SPRINT_FIELD_FALLBACKS,
        HIERARCHY_RULES,
        CLOSED_STATUSES,
    )

    # Verify constants are defined with expected types
    assert isinstance(JIRA_BASE_URL, str)
    assert isinstance(MAX_IMAGE_SIZE, int)
    assert isinstance(MAX_TEXT_SIZE, int)
    assert isinstance(MAX_PDF_SIZE, int)
    assert isinstance(IMAGE_TYPES, set)
    assert isinstance(TEXT_TYPES, set)
    assert SPRINT_FIELD_ID is None  # starts as None, discovered at runtime
    assert isinstance(_SPRINT_FIELD_FALLBACKS, list)
    assert isinstance(HIERARCHY_RULES, dict)
    assert isinstance(CLOSED_STATUSES, set)


def test_size_limits():
    """Test that size limits are reasonable."""
    from config import MAX_IMAGE_SIZE, MAX_TEXT_SIZE, MAX_PDF_SIZE

    assert MAX_IMAGE_SIZE == 10 * 1024 * 1024  # 10MB
    assert MAX_TEXT_SIZE == 5 * 1024 * 1024    # 5MB
    assert MAX_PDF_SIZE == 20 * 1024 * 1024    # 20MB


def test_mime_types():
    """Test MIME type categories."""
    from config import IMAGE_TYPES, TEXT_TYPES

    assert "image/png" in IMAGE_TYPES
    assert "image/jpeg" in IMAGE_TYPES
    assert "text/plain" in TEXT_TYPES
    assert "application/json" in TEXT_TYPES


def test_closed_statuses():
    """Test closed status definitions."""
    from config import CLOSED_STATUSES

    expected = {"closed", "done", "resolved", "cancelled", "rejected"}
    assert CLOSED_STATUSES == expected
