"""Configuration and constants for Confluence MCP Server."""
import os
from typing import Optional

from dotenv import load_dotenv

load_dotenv()

# Confluence connection settings
CONFLUENCE_BASE_URL = os.getenv("CONFLUENCE_BASE_URL", "https://api.skyway.porsche.com/confluence")
CONFLUENCE_PAT = os.getenv("CONFLUENCE_PAT")

if not CONFLUENCE_PAT:
    raise RuntimeError("CONFLUENCE_PAT environment variable is not set")

# Certificate authentication (optional - disabled by default)
CERT_PATH: Optional[str] = os.getenv("CERT_PATH")
CERT_PASSWORD: Optional[str] = os.getenv("CERT_PASSWORD")

# Proxy configuration (used when certificate auth is not configured)
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

# MCP transport mode: "http" (default) or "stdio"
MCP_TRANSPORT = os.getenv("MCP_TRANSPORT", "http").lower()

print(f"[confluence-mcp] Confluence Base URL: {CONFLUENCE_BASE_URL}")
print(f"[confluence-mcp] MCP transport: {MCP_TRANSPORT}")
if PROXIES:
    print("[confluence-mcp] Proxy configuration available")
