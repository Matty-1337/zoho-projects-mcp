"""
Zoho OAuth2 token management for Zoho Projects MCP server.
Handles refresh token flow to maintain valid access tokens.
"""

import os
import time
import httpx
from typing import Optional

# Token cache
_access_token: Optional[str] = None
_token_expiry: float = 0

ZOHO_ACCOUNTS_URL = os.environ.get("ZOHO_ACCOUNTS_URL", "https://accounts.zoho.com")
CLIENT_ID = os.environ.get("ZOHO_CLIENT_ID", "")
CLIENT_SECRET = os.environ.get("ZOHO_CLIENT_SECRET", "")
REFRESH_TOKEN = os.environ.get("ZOHO_REFRESH_TOKEN", "")
PORTAL_ID = os.environ.get("ZOHO_PORTAL_ID", "868784641")

BASE_URL = "https://projectsapi.zoho.com/api/v3"


async def get_access_token() -> str:
    """Get a valid access token, refreshing if necessary."""
    global _access_token, _token_expiry

    if _access_token and time.time() < _token_expiry - 60:
        return _access_token

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
            raise ValueError(f"Failed to get access token: {data}")

        _access_token = data["access_token"]
        _token_expiry = time.time() + data.get("expires_in", 3600)
        return _access_token


async def zoho_request(
    method: str,
    endpoint: str,
    params: Optional[dict] = None,
    json: Optional[dict] = None,
    data: Optional[dict] = None,
) -> dict:
    """Make an authenticated request to the Zoho Projects API."""
    token = await get_access_token()
    url = f"{BASE_URL}{endpoint}"

    headers = {
        "Authorization": f"Zoho-oauthtoken {token}",
        "Content-Type": "application/json",
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.request(
            method=method,
            url=url,
            headers=headers,
            params=params,
            json=json,
            data=data,
        )

        if response.status_code == 204:
            return {"success": True}

        try:
            result = response.json()
        except Exception:
            result = {"raw": response.text}

        if not response.is_success:
            raise httpx.HTTPStatusError(
                f"API error {response.status_code}: {result}",
                request=response.request,
                response=response,
            )

        return result


def handle_error(e: Exception) -> str:
    """Format errors into clear, actionable messages."""
    if isinstance(e, httpx.HTTPStatusError):
        status = e.response.status_code if hasattr(e, 'response') else 'unknown'
        if status == 404:
            return f"Error: Resource not found. Check the ID is correct. Details: {str(e)}"
        elif status == 403:
            return f"Error: Permission denied. Check OAuth scopes. Details: {str(e)}"
        elif status == 429:
            return "Error: Rate limit exceeded. Please wait before retrying."
        elif status == 401:
            return "Error: Unauthorized. OAuth token may be invalid or expired."
        return f"Error: API request failed (HTTP {status}): {str(e)}"
    elif isinstance(e, httpx.TimeoutException):
        return "Error: Request timed out. Please try again."
    elif isinstance(e, ValueError):
        return f"Error: {str(e)}"
    return f"Error: Unexpected error ({type(e).__name__}): {str(e)}"
