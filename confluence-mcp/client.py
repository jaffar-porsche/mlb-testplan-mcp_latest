"""Confluence client initialization with optional certificate authentication."""
import requests
from atlassian import Confluence

from config import CONFLUENCE_BASE_URL, CONFLUENCE_PAT, PROXIES, CERT_PATH, CERT_PASSWORD
from cert_loader import cert_manager, validate_openssl_available

_confluence_client = None


def _create_confluence_client() -> Confluence:
    """
    Create Confluence client with appropriate authentication.

    Authentication priority:
    1. Certificate + PAT (if CERT_PATH and CERT_PASSWORD are set)
    2. PAT-only with proxy (fallback)
    """
    if CERT_PATH and CERT_PASSWORD:
        print("[confluence-mcp] Attempting certificate-based authentication...")
        print(f"[confluence-mcp] Certificate path: {CERT_PATH}")

        try:
            if not validate_openssl_available():
                raise RuntimeError(
                    "OpenSSL is required for certificate-based authentication "
                    "but is not available"
                )

            cert_tuple = cert_manager.setup_certificate(CERT_PATH, CERT_PASSWORD)

            session = requests.Session()
            session.cert = cert_tuple
            session.headers.update({
                "Content-Type": "application/json",
                "Authorization": f"Bearer {CONFLUENCE_PAT}"
            })

            response = session.get(
                f"{CONFLUENCE_BASE_URL}/rest/api/user/current",
                timeout=10
            )
            if response.status_code == 200:
                user_info = response.json()
                print("[confluence-mcp] Certificate-based authentication successful")
                print(f"[confluence-mcp] Authenticated as: {user_info.get('displayName', 'Unknown')}")

                return Confluence(
                    url=CONFLUENCE_BASE_URL,
                    token=CONFLUENCE_PAT,
                    session=session
                )
            else:
                raise RuntimeError(
                    f"Authentication test failed with status {response.status_code}"
                )

        except Exception as e:
            print(f"[confluence-mcp] Certificate-based authentication failed: {e}")
            print("[confluence-mcp] Falling back to PAT-only authentication...")

    print("[confluence-mcp] Using PAT-only authentication...")
    return Confluence(
        url=CONFLUENCE_BASE_URL,
        token=CONFLUENCE_PAT,
        proxies=PROXIES
    )


def get_confluence_client() -> Confluence:
    """Get or create the Confluence client (lazy initialization)."""
    global _confluence_client
    if _confluence_client is None:
        _confluence_client = _create_confluence_client()
    return _confluence_client


class _ConfluenceClientProxy:
    """Proxy class to allow lazy initialization while supporting attribute access."""

    def __getattr__(self, name):
        return getattr(get_confluence_client(), name)

    def __repr__(self):
        return repr(get_confluence_client())


confluence = _ConfluenceClientProxy()
