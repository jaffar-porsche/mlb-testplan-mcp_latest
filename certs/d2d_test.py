from __future__ import annotations
 
import logging
import os
import time
from dataclasses import dataclass, field
from typing import Optional
 
import requests
from dotenv import load_dotenv
from msal import ConfidentialClientApplication
 
logger = logging.getLogger(__name__)

# Same corporate proxy used elsewhere in this repo (server.py). MSAL's HTTP
# client (requests) does not automatically pick up HTTP_PROXY/HTTPS_PROXY in
# every process context (e.g. when the server is launched via a debugger or
# a shell that hasn't set these vars), so we wire it in explicitly here.
_PROXY = os.getenv("HTTP_PROXY", "http://http-proxy.porsche.org:3133")


def _build_http_session() -> requests.Session:
    session = requests.Session()
    if _PROXY:
        session.proxies.update({"http": _PROXY, "https": _PROXY})
    return session
 
 
@dataclass
class D2DSallyTokenProvider:
    """Acquire and cache a daemon-to-daemon access token for Sally APIs."""
 
    backend_app_id: str
    backend_app_client_secret: str
    tenant_id: str
    third_party_app_id: str
    refresh_leeway_seconds: int = 120
    _access_token: Optional[str] = field(default=None, init=False, repr=False)
    _expires_at: float = field(default=0.0, init=False, repr=False)
 
    @property
    def authority(self) -> str:
        return f"https://login.microsoftonline.com/{self.tenant_id}"
 
    @property
    def scope(self) -> str:
        return f"api://{self.third_party_app_id}/.default"
 
    def _is_token_valid(self) -> bool:
        if not self._access_token:
            return False
        return time.time() < (self._expires_at - self.refresh_leeway_seconds)
 
    def _acquire_new_token(self) -> str:
        client = ConfidentialClientApplication(
            self.backend_app_id,
            client_credential=self.backend_app_client_secret,
            authority=self.authority,
            http_client=_build_http_session(),
        )
        token = client.acquire_token_for_client(scopes=[self.scope])
        if "access_token" not in token:
            message = token.get("error_description") or token.get("error") or "Unknown MSAL error"
            raise RuntimeError(f"Failed to acquire Sally D2D token: {message}")
        self._access_token = token["access_token"]
        self._expires_at = time.time() + int(token.get("expires_in", 3600))
       
        # Log token details
        logger.debug(f"D2D token acquired successfully for app_id={self.backend_app_id}")
        logger.debug(f"D2D token expires in {token.get('expires_in', 3600)} seconds")
       
        return self._access_token
 
    def get_token(self) -> str:
        if self._is_token_valid():
            return self._access_token or ""
        return self._acquire_new_token()


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

    provider = D2DSallyTokenProvider(
        backend_app_id=os.environ["BACKEND_APP_ID"],
        backend_app_client_secret=os.environ["BACKEND_APP_CLIENT_SECRET"],
        tenant_id=os.environ["TENANT_ID"],
        third_party_app_id=os.environ["THIRD_PARTY_APP_ID"],
    )

    print("Testing D2D token acquisition...")
    token = provider.get_token()
    print(f"Token acquired ({len(token)} chars). First 20 chars: {token}...")


if __name__ == "__main__":
    main()