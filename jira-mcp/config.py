"""Configuration and constants for Jira MCP Server."""
import os
from typing import Set, Optional

from dotenv import load_dotenv

load_dotenv()

# Jira connection settings
JIRA_BASE_URL = os.getenv("JIRA_BASE_URL", "https://api.skyway.porsche.com/jira")
JIRA_PAT = os.getenv("JIRA_PAT")

if not JIRA_PAT:
    raise RuntimeError("JIRA_PAT environment variable is not set")

# Certificate authentication (optional - disabled by default)
# Set CERT_PATH and CERT_PASSWORD to enable certificate-based authentication
CERT_PATH: Optional[str] = os.getenv("CERT_PATH")
CERT_PASSWORD: Optional[str] = os.getenv("CERT_PASSWORD")

# Proxy configuration (only used when HTTP_PROXY / HTTPS_PROXY are set)
# When using devx-cli proxy, set JIRA_BASE_URL to http://127.0.0.1:19091
# and leave proxy settings unset.
_http_proxy = os.getenv("HTTP_PROXY")
_https_proxy = os.getenv("HTTPS_PROXY")
if _http_proxy or _https_proxy:
    PROXIES = {}
    if _http_proxy:
        PROXIES["http"] = _http_proxy
    if _https_proxy:
        PROXIES["https"] = _https_proxy
else:
    PROXIES = None

# Agile API base URL
JIRA_AGILE_BASE = f"{JIRA_BASE_URL}/rest/agile/1.0"

# Service Desk API base URL
JIRA_SD_BASE = f"{JIRA_BASE_URL}/rest/servicedeskapi"

# xRay REST API base URL (v2.0)
XRAY_BASE_URL = f"{JIRA_BASE_URL}/rest/raven/2.0"

# Attachment download size limits
MAX_IMAGE_SIZE = 10 * 1024 * 1024   # 10MB
MAX_TEXT_SIZE = 5 * 1024 * 1024      # 5MB
MAX_PDF_SIZE = 20 * 1024 * 1024     # 20MB

# MIME type categories
IMAGE_TYPES: Set[str] = {
    "image/png", "image/jpeg", "image/gif", "image/webp",
    "image/bmp", "image/svg+xml"
}
TEXT_TYPES: Set[str] = {
    "text/plain", "text/csv", "text/html", "text/xml",
    "application/json", "application/xml"
}

# MCP transport mode: "http" (default) or "stdio"
MCP_TRANSPORT = os.getenv("MCP_TRANSPORT", "http").lower()

# Sprint custom field ID - discovered dynamically at startup, falls back to common defaults
SPRINT_FIELD_ID: str | None = None

# Fallback sprint field IDs (varies by Jira instance) - used only if discovery fails
_SPRINT_FIELD_FALLBACKS = [
    "customfield_10020",
    "customfield_10104",
    "customfield_10007",
    "customfield_10100",
    "customfield_10004",
]

# Hierarchy type filtering rules (prevents circular references)
HIERARCHY_RULES = {
    "portfolio epic": {"feature"},
    "epic": {"feature", "story", "user story", "task"},
    "feature": {"story", "user story", "task", "enabler"},
    "story": {"task", "sub-task"},
    "user story": {"task", "sub-task"},
}

# Statuses considered "closed" for filtering
CLOSED_STATUSES: Set[str] = {
    "closed", "done", "resolved", "cancelled", "rejected"
}
