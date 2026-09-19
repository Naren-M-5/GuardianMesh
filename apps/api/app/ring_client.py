from __future__ import annotations

from typing import Any
from urllib.parse import quote

import httpx


class RingApiError(RuntimeError):
    """Raised when the Ring API cannot serve a request."""


def _get(access_token: str, url: str, params: dict[str, str] | None = None) -> dict[str, Any]:
    if not access_token:
        raise RingApiError(
            "Ring access token is not configured. Add GUARDIANMESH_RING_ACCESS_TOKEN to .env."
        )
    try:
        response = httpx.get(
            url,
            headers={"Authorization": f"Bearer {access_token}"},
            params=params,
            timeout=15.0,
        )
        response.raise_for_status()
        return response.json()
    except httpx.HTTPStatusError as exc:
        status = exc.response.status_code
        if status == 401:
            raise RingApiError(
                "Ring access token expired or is invalid. Generate a fresh Playground token."
            ) from exc
        if status == 429:
            raise RingApiError("Ring API rate limit reached. Wait briefly and try again.") from exc
        raise RingApiError(f"Ring API returned HTTP {status}.") from exc
    except (httpx.HTTPError, ValueError) as exc:
        raise RingApiError("Could not connect to the Ring API.") from exc


def list_devices(access_token: str, base_url: str = "https://api.amazonvision.com") -> dict[str, Any]:
    """Return devices visible to the token without logging or persisting it."""
    return _get(access_token, f"{base_url.rstrip('/')}/v1/devices")


def list_device_events(
    access_token: str,
    device_id: str,
    base_url: str = "https://api.amazonvision.com",
    event_types: str = "ding,on_demand,motion",
) -> dict[str, Any]:
    """Return the newest Ring event-history page for one authorized device."""
    if not device_id:
        raise RingApiError("Ring device ID is missing.")
    directed_id = quote(device_id, safe="")
    return _get(
        access_token,
        f"{base_url.rstrip('/')}/v1/history/devices/{directed_id}/events",
        {"event_types": event_types},
    )
