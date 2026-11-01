"""HTTP client for the cgotchi Home Assistant API."""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any, Callable

from .settings import Settings

Transport = Callable[[urllib.request.Request], tuple[int, bytes]]


class ApiError(Exception):
    def __init__(self, status: int, message: str) -> None:
        super().__init__(f"HTTP {status}: {message}" if status else message)
        self.status = status


def urllib_transport(request: urllib.request.Request) -> tuple[int, bytes]:
    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            return response.status, response.read()
    except urllib.error.HTTPError as err:
        return err.code, err.read()
    except OSError as err:
        raise ApiError(0, f"cannot reach Home Assistant: {err}") from err


class CgotchiClient:
    def __init__(self, settings: Settings, transport: Transport = urllib_transport) -> None:
        self._settings = settings
        self._transport = transport

    def _request(self, method: str, path: str, body: dict[str, Any] | None = None) -> Any:
        data = None if body is None else json.dumps(body).encode()
        request = urllib.request.Request(
            f"{self._settings.url}/api/cgotchi/{path}",
            data=data,
            method=method,
            headers={"Authorization": f"Bearer {self._settings.token}", "Content-Type": "application/json"},
        )
        status, payload = self._transport(request)
        if status >= 400:
            raise ApiError(status, _message(payload))
        try:
            return json.loads(payload)
        except ValueError as err:
            raise ApiError(status, f"reply is not JSON: {payload[:80]!r}") from err

    def state(self) -> Any:
        return self._request("GET", "state")

    def touch(self) -> Any:
        return self._request("GET", "touch")

    def get_display(self) -> Any:
        return self._request("GET", "display")

    def set_display(self, **fields: Any) -> Any:
        return self._request("POST", "display", fields)

    def get_speaker(self) -> Any:
        return self._request("GET", "speaker")

    def set_speaker(self, **fields: Any) -> Any:
        return self._request("POST", "speaker", fields)

    def set_wake_word(self, enabled: bool) -> Any:
        return self._request("POST", "voice", {"wake_word_mode": enabled})


def _message(payload: bytes) -> str:
    try:
        return json.loads(payload).get("message", "")
    except (ValueError, AttributeError):
        return payload.decode(errors="replace")[:200]
