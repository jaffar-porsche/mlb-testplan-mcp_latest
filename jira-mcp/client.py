"""Jira client initialization with optional certificate authentication.

Exports:
    jira         - Lazy-initialized JIRA library client (for jira-python API calls)
    http_session - Pre-configured requests.Session with the same auth (cert or proxy)
                   for direct REST calls that bypass the jira library.
"""

import requests
from jira import JIRA

from config import JIRA_BASE_URL, JIRA_PAT, PROXIES, CERT_PATH, CERT_PASSWORD
from cert_loader import cert_manager, validate_openssl_available

# Global Jira client (lazy initialization)
_jira_client = None

# Global HTTP session (lazy initialization, shares auth config with jira client)
_http_session = None


def _create_http_session(cert_tuple=None) -> requests.Session:
    """Create a requests.Session pre-configured with auth.

    When cert_tuple is provided, the session uses mTLS (no proxy).
    Otherwise it uses PAT + proxy, matching the jira client behaviour.
    """
    session = requests.Session()
    session.headers.update(
        {
            "Authorization": f"Bearer {JIRA_PAT}",
            "Content-Type": "application/json",
        }
    )
    if cert_tuple:
        session.cert = cert_tuple
    elif PROXIES:
        session.proxies.update(PROXIES)
    return session


def _create_jira_client() -> JIRA:
    """
    Create Jira client with appropriate authentication.

    Authentication priority:
    1. Certificate + PAT (if CERT_PATH and CERT_PASSWORD are set)
    2. PAT-only with proxy (fallback)

    Side effect: also initialises the global _http_session.

    Returns:
        Configured JIRA client instance
    """
    global _http_session

    # Try certificate-based authentication first
    if CERT_PATH and CERT_PASSWORD:
        print("[jira-mcp] Attempting certificate-based authentication...")
        print(f"[jira-mcp] Certificate path: {CERT_PATH}")

        try:
            # Validate OpenSSL is available
            if not validate_openssl_available():
                raise RuntimeError(
                    "OpenSSL is required for certificate-based authentication "
                    "but is not available"
                )

            # Extract certificate and key from P12 file
            cert_tuple = cert_manager.setup_certificate(CERT_PATH, CERT_PASSWORD)

            # Create shared HTTP session with certificate
            _http_session = _create_http_session(cert_tuple=cert_tuple)

            # Test the connection using the shared session
            response = _http_session.get(
                f"{JIRA_BASE_URL}/rest/api/2/myself", timeout=10
            )
            if response.status_code == 200:
                user_info = response.json()
                print("[jira-mcp] Certificate-based authentication successful")
                print(
                    f"[jira-mcp] Authenticated as: {user_info.get('displayName', 'Unknown')}"
                )

                # Create JIRA client with custom options for cert auth
                # Note: jira library uses requests internally, we configure via options
                return JIRA(
                    server=JIRA_BASE_URL,
                    token_auth=JIRA_PAT,
                    options={"verify": True, "client_cert": cert_tuple},
                )
            else:
                raise RuntimeError(
                    f"Authentication test failed with status {response.status_code}"
                )

        except Exception as e:
            print(f"[jira-mcp] Certificate-based authentication failed: {e}")
            print("[jira-mcp] Falling back to PAT-only authentication...")

    # Fall back to PAT-only authentication (with proxy)
    print("[jira-mcp] Using PAT-only authentication with proxy...")
    _http_session = _create_http_session()
    return JIRA(server=JIRA_BASE_URL, token_auth=JIRA_PAT, proxies=PROXIES)


def get_jira_client() -> JIRA:
    """
    Get or create the Jira client (lazy initialization).

    Returns:
        Configured JIRA client instance
    """
    global _jira_client
    if _jira_client is None:
        _jira_client = _create_jira_client()
    return _jira_client


def get_http_session() -> requests.Session:
    """Get the shared HTTP session (lazy initialization).

    Triggers jira client creation if not yet initialised, because the
    session auth config (cert vs proxy) is determined during that step.
    """
    global _http_session
    if _http_session is None:
        get_jira_client()  # side-effect: populates _http_session
    assert _http_session is not None  # guaranteed by _create_jira_client
    return _http_session


# Expose as module-level variable for backwards compatibility
class _JiraClientProxy:
    """Proxy class to allow lazy initialization while supporting attribute access."""

    def __getattr__(self, name):
        return getattr(get_jira_client(), name)

    def __repr__(self):
        return repr(get_jira_client())


class _HttpSessionProxy:
    """Proxy class to allow lazy initialization of the HTTP session."""

    def __getattr__(self, name):
        return getattr(get_http_session(), name)

    def __repr__(self):
        return repr(get_http_session())


jira = _JiraClientProxy()
http_session = _HttpSessionProxy()
