"""HTTP API under /api/cgotchi. The data views need an admin's Home Assistant token; only the spec is public."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any, Awaitable, Callable

import voluptuous as vol
import yaml
from aiohttp import web
from homeassistant.components.http import HomeAssistantView
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError, ServiceNotFound, ServiceValidationError

from .const import DOMAIN
from .device import CgotchiDevice, EntityNotFound
from .schemas import DISPLAY_SCHEMA, SPEAKER_SCHEMA, VOICE_SCHEMA

_DIR = Path(__file__).parent
_SPEC = _DIR / "openapi.yaml"

def _async(fn: Callable[[CgotchiDevice], Any]) -> Callable[[CgotchiDevice], Awaitable[Any]]:
    async def run(device: CgotchiDevice) -> Any:
        return fn(device)

    return run

class _CgotchiView(HomeAssistantView):
    """Shared plumbing: 403 for non-admins, 503 without a device, 400 on bad input, 404/502 from the device."""

    async def _run(self, request: web.Request, action: Callable[[CgotchiDevice], Awaitable[Any]]) -> web.Response:
        user = request.get("hass_user")
        if user is None or not user.is_admin:
            return self.json_message("administrator token required", 403)
        device: CgotchiDevice | None = request.app["hass"].data.get(DOMAIN)
        if device is None:
            return self.json_message("cgotchi is not set up", 503)
        try:
            return self.json(await action(device))
        except EntityNotFound as err:
            return self.json_message(str(err), 404)
        except ServiceNotFound as err:
            return self.json_message(f"service not available: {err}", 404)
        except (ServiceValidationError, vol.Invalid) as err:
            return self.json_message(f"device rejected the request: {err}", 400)
        except HomeAssistantError as err:
            return self.json_message(str(err), 502)

    async def _post(
        self,
        request: web.Request,
        schema: Callable[[Any], dict[str, Any]],
        apply: Callable[[CgotchiDevice, dict[str, Any]], Awaitable[None]],
        read: Callable[[CgotchiDevice], Any],
    ) -> web.Response:
        try:
            body = schema(await request.json())
        except (ValueError, vol.Invalid) as err:
            return self.json_message(f"invalid request: {err}", 400)

        async def run(device: CgotchiDevice) -> Any:
            await apply(device, body)
            return read(device)

        return await self._run(request, run)

class DisplayView(_CgotchiView):
    url = "/api/cgotchi/display"
    name = "api:cgotchi:display"

    async def get(self, request: web.Request) -> web.Response:
        return await self._run(request, _async(lambda d: d.display_state()))

    async def post(self, request: web.Request) -> web.Response:
        return await self._post(request, DISPLAY_SCHEMA, CgotchiDevice.apply_display, CgotchiDevice.display_state)

class SpeakerView(_CgotchiView):
    url = "/api/cgotchi/speaker"
    name = "api:cgotchi:speaker"

    async def get(self, request: web.Request) -> web.Response:
        return await self._run(request, _async(lambda d: d.speaker_state()))

    async def post(self, request: web.Request) -> web.Response:
        return await self._post(request, SPEAKER_SCHEMA, CgotchiDevice.apply_speaker, CgotchiDevice.speaker_state)

class VoiceView(_CgotchiView):
    url = "/api/cgotchi/voice"
    name = "api:cgotchi:voice"

    async def get(self, request: web.Request) -> web.Response:
        return await self._run(request, _async(lambda d: d.voice_state()))

    async def post(self, request: web.Request) -> web.Response:
        return await self._post(request, VOICE_SCHEMA, CgotchiDevice.apply_voice, CgotchiDevice.voice_state)

class TouchView(_CgotchiView):
    url = "/api/cgotchi/touch"
    name = "api:cgotchi:touch"

    async def get(self, request: web.Request) -> web.Response:
        return await self._run(request, _async(lambda d: d.touch_state()))

class StateView(_CgotchiView):
    url = "/api/cgotchi/state"
    name = "api:cgotchi:state"

    async def get(self, request: web.Request) -> web.Response:
        return await self._run(
            request,
            _async(
                lambda d: {
                    "display": d.display_state(),
                    "speaker": d.speaker_state(),
                    "voice": d.voice_state(),
                    "touch": d.touch_state(),
                }
            ),
        )

@lru_cache(maxsize=1)
def _spec_json(modified: float) -> str:
    """Parsed once per file version; `modified` is only the cache key."""
    return json.dumps(yaml.safe_load(_SPEC.read_text("utf-8")))

class OpenApiView(HomeAssistantView):
    """The spec is public documentation, so it needs no token."""

    url = "/api/cgotchi/openapi.json"
    name = "api:cgotchi:openapi"
    requires_auth = False

    async def get(self, request: web.Request) -> web.Response:
        hass: HomeAssistant = request.app["hass"]
        text = await hass.async_add_executor_job(lambda: _spec_json(_SPEC.stat().st_mtime))
        return web.Response(text=text, content_type="application/json")

VIEWS = [DisplayView, SpeakerView, VoiceView, TouchView, StateView, OpenApiView]
