"""Pytest fixtures and configuration."""
import os
import sys
from unittest.mock import MagicMock

# Set required env vars before any imports
os.environ["JIRA_PAT"] = "test-token"
os.environ["JIRA_BASE_URL"] = "https://test.jira.local"
os.environ["HTTP_PROXY"] = ""
os.environ["HTTPS_PROXY"] = ""

# Mock jira module BEFORE any app modules import it
_mock_jira_instance = MagicMock()
_mock_jira_instance.server_info.return_value = {"serverTitle": "Test Jira"}

_mock_jira_module = MagicMock()
_mock_jira_module.JIRA.return_value = _mock_jira_instance

# Pre-populate sys.modules with mock
sys.modules["jira"] = _mock_jira_module
