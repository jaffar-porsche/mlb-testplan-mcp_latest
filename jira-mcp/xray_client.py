"""xRay client initialization with optional certificate authentication.

Uses the xRay Server/DC REST API v2.0:
  {JIRA_BASE_URL}/rest/raven/2.0/api/...

Authentication reuses the same Jira PAT and optional P12 certificate
already configured in config.py.
"""
import requests

from config import XRAY_BASE_URL, JIRA_PAT, PROXIES, CERT_PATH, CERT_PASSWORD
from cert_loader import cert_manager, validate_openssl_available

# Global session (lazy initialization)
_xray_session = None


def _create_xray_session() -> requests.Session:
    """
    Create a requests.Session configured for the xRay REST API.

    Authentication priority:
    1. Certificate + PAT (if CERT_PATH and CERT_PASSWORD are set)
    2. PAT-only with proxy (fallback)

    Returns:
        Configured requests.Session instance
    """
    # Try certificate-based authentication first
    if CERT_PATH and CERT_PASSWORD:
        print("[xray-client] Attempting certificate-based authentication...")
        print(f"[xray-client] Certificate path: {CERT_PATH}")

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
                "Accept": "application/json",
                "Authorization": f"Bearer {JIRA_PAT}",
            })

            # Verify connectivity with a lightweight xRay endpoint
            response = session.get(
                f"{XRAY_BASE_URL}/api/settings/teststatuses",
                timeout=10
            )
            if response.status_code in (200, 401, 403):
                # 401/403 means the server is reachable (auth checked separately)
                print("[xray-client] Certificate-based session established")
                return session
            raise RuntimeError(
                f"Connectivity check failed with status {response.status_code}"
            )

        except Exception as e:
            print(f"[xray-client] Certificate-based authentication failed: {e}")
            print("[xray-client] Falling back to PAT-only authentication...")

    # PAT-only authentication
    print("[xray-client] Using PAT-only authentication...")
    session = requests.Session()
    session.headers.update({
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Authorization": f"Bearer {JIRA_PAT}",
    })
    if PROXIES:
        session.proxies.update(PROXIES)
    return session


class _XRayClientProxy:
    """Lazy proxy for the xRay requests.Session.

    Initializes the session on first attribute access so startup is fast
    and cert loading only happens when xRay routes are actually called.
    """

    _session: requests.Session | None = None

    def _get_session(self) -> requests.Session:
        if self._session is None:
            self._session = _create_xray_session()
        return self._session

    def get(self, url: str, **kwargs) -> requests.Response:
        return self._get_session().get(url, **kwargs)

    def post(self, url: str, **kwargs) -> requests.Response:
        return self._get_session().post(url, **kwargs)

    def put(self, url: str, **kwargs) -> requests.Response:
        return self._get_session().put(url, **kwargs)

    def delete(self, url: str, **kwargs) -> requests.Response:
        return self._get_session().delete(url, **kwargs)


xray = _XRayClientProxy()
