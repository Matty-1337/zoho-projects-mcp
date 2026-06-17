import os
import time
import httpx
from typing import Optional

_access_token: Optional[str] = None
_token_expiry: float = 0

ZOHO_ACCOUNTS_URL = os.environ.get("ZOHO_ACCOUNTS_URL", "https://accounts.zoho.com")
CLIENT_ID = os.environ.get("ZOHO_CLIENT_ID", "")
CLIENT_SECRET = os.environ.get("ZOHO_CLIENT_SECRET", "")
REFRESH_TOKEN = os.environ.get("ZOHO_REFRESH_TOKEN", "")
PORTAL_ID = os.environ.get("ZOHO_PORTAL_ID", "868784641")

BASE_URL = "https://projectsapi.zoho.com/api/v3"


def _set_access_token(token: str, expiry: float):
    global _access_token, _token_expiry
    _access_token = token
    _token_expiry = expiry


async def get_access_token(force_refresh: bool = False) -> str:
    global _access_token, _token_expiry

    if not force_refresh and _access_token and time.time() < _token_expiry - 60:
        return _access_token

    if not REFRESH_TOKEN:
        raise ValueError("No refresh token. Visit https://zoho-projects-mcp-production.up.railway.app/auth")

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{ZOHO_ACCOUNTS_URL}/oauth/v2/token",
            data={
                "refresh_token": REFRESH_TOKEN,
                "client_id": CLIENT_ID,
                "client_secret": CLIENT_SECRET,
                "grant_type": "refresh_token",
            },
        )
        response.raise_for_status()
        data = response.json()
        if "access_token" not in data:
            raise ValueError(f"Token error: {data}")
        _access_token = data["access_token"]
        _token_expiry = time.time() + data.get("expires_in", 3600)
        return _access_token


async def zoho_request(method: str, endpoint: str, params=None, json=None, data=None) -> dict:
    token = await get_access_token()
    url = f"{BASE_URL}{endpoint}"
    headers = {"Authorization": f"Zoho-oauthtoken {token}", "Content-Type": "application/json"}

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.request(method=method, url=url, headers=headers, params=params, json=json, data=data)

        # If 401, force refresh token and retry once
        if response.status_code == 401:
            token = await get_access_token(force_refresh=True)
            headers["Authorization"] = f"Zoho-oauthtoken {token}"
            response = await client.request(method=method, url=url, headers=headers, params=params, json=json, data=data)

        if response.status_code == 204:
            return {"success": True}
        try:
            result = response.json()
        except Exception:
            result = {"raw": response.text}
        if not response.is_success:
            raise httpx.HTTPStatusError(f"API error {response.status_code}: {result}", request=response.request, response=response)
        return result


def handle_error(e: Exception) -> str:
    if isinstance(e, httpx.HTTPStatusError):
        status = e.response.status_code if hasattr(e, 'response') else 'unknown'
        if status == 404: return f"Error: Resource not found. {str(e)}"
        if status == 403: return f"Error: Permission denied. {str(e)}"
        if status == 429: return "Error: Rate limit exceeded."
        if status == 401: return "Error: Unauthorized even after token refresh. Check credentials."
        return f"Error: API failed (HTTP {status}): {str(e)}"
    if isinstance(e, httpx.TimeoutException): return "Error: Request timed out."
    return f"Error: {type(e).__name__}: {str(e)}"
