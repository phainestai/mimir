"""
HTTP client module for the MCP facade.

Provides a shared httpx.Client instance configured with
the server URL and token from the facade's startup arguments.
"""
import logging
import httpx

logger = logging.getLogger(__name__)

_server_url: str = ""
_token: str = ""
_http_client: httpx.Client | None = None


def configure(server_url: str, token: str) -> None:
    """
    Configure the shared HTTP client.

    :param server_url: Base URL of the Mimir REST API. Example: "http://localhost:8000"
    :param token: DRF auth token. Example: "abc123def456"
    """
    global _server_url, _token, _http_client
    _server_url = server_url.rstrip("/")
    _token = token
    _http_client = httpx.Client(
        base_url=_server_url,
        headers={
            "Authorization": f"Token {_token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
        timeout=30.0,
    )
    logger.info(f"HTTP client configured: server={_server_url}")


def get_client() -> httpx.Client:
    """
    Get the configured HTTP client.

    :return: Configured httpx.Client
    :raises RuntimeError: if configure() has not been called
    """
    if _http_client is None:
        raise RuntimeError("HTTP client not configured. Call configure() first.")
    return _http_client


def check_response(response: httpx.Response, tool_name: str) -> dict:
    """
    Validate HTTP response and return parsed JSON.

    :param response: httpx response object
    :param tool_name: MCP tool name for logging
    :return: Parsed response body as dict or list
    :raises ValueError: for 4xx errors (not found, validation, etc.)
    :raises PermissionError: for 403 errors
    :raises RuntimeError: for 5xx errors
    """
    logger.debug(f"{tool_name}: HTTP {response.status_code} from {response.url}")

    if response.status_code in (200, 201, 204):
        if response.status_code == 204 or not response.content:
            return {"deleted": True}
        return response.json()

    try:
        body = response.json()
        error_msg = body.get("error") or body.get("detail") or str(body)
    except Exception:
        error_msg = response.text or f"HTTP {response.status_code}"

    if response.status_code == 403:
        raise PermissionError(f"{tool_name}: {error_msg}")
    if response.status_code in (400, 404, 409):
        raise ValueError(f"{tool_name}: {error_msg}")
    raise RuntimeError(f"{tool_name}: HTTP {response.status_code} — {error_msg}")
