from __future__ import annotations

from typing import Any

import httpx


class RingApiError(RuntimeError):
    """Raised when the Ring API cannot serve a request."""


def list_devices(access_token: str, base_url: str = "https://api.amazonvision.com") -> dict[str, Any]:
    """Return the devices visible to the current Ring access token.

    Tokens are supplied by the caller and are never logged or persisted.
    """
    if not access_token:
        raise RingApiError(
            "Ring access token is not configured. Add GUARDIANMESH_RING_ACCESS_TOKEN to .env."
        )

    try:
        response = httpx.get(
            f"{base_url.rstrip('/')}/v1/devices",
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=15.0,
        )
        response.raise_for_status()
        return response.json()
    except httpx.HTTPStatusError as exc:
        raise RingApiError(f"Ring API returned HTTP {exc.response.status_code}.") from exc
    except httpx.HTTPError as exc:
        raise RingApiError("Could not connect to the Ring API.") from exc
