"""The cgotchi device as Home Assistant entities: find them by name, call their services, read their state."""

from __future__ import annotations

from typing import Any

from homeassistant.core import HomeAssistant, State
from homeassistant.helpers import entity_registry as er

from .const import DISPLAY_FIELDS, TOUCH_ENTITIES
from .schemas import display_in_order


class EntityNotFound(Exception):
    """The device has no entity with this name (firmware older than the API, or entity disabled)."""


Call = tuple[str, str, dict[str, Any]]


class CgotchiDevice:
    def __init__(self, hass: HomeAssistant, device_id: str) -> None:
        self._hass = hass
        self._device_id = device_id

    def entity_id(self, domain: str, name: str) -> str:
        registry = er.async_get(self._hass)
        for entry in er.async_entries_for_device(registry, self._device_id):
            if entry.domain == domain and name in (entry.original_name, entry.name):
                return entry.entity_id
        raise EntityNotFound(f"{domain} '{name}' not found on the device")

    async def _run(self, calls: list[Call]) -> None:
        """Calls are built first, so a missing entity fails before anything is changed."""
        for domain, service, data in calls:
            await self._hass.services.async_call(domain, service, data, blocking=True)

    async def apply_display(self, body: dict[str, Any]) -> None:
        calls: list[Call] = []
        for field, value in display_in_order(body):
            domain, name = DISPLAY_FIELDS[field]
            entity_id = self.entity_id(domain, name)
            if domain == "select":
                calls.append(("select", "select_option", {"entity_id": entity_id, "option": value}))
            elif domain == "light":
                calls.append(("light", "turn_on", {"entity_id": entity_id, "rgb_color": value}))
            else:
                calls.append((domain, "set_value", {"entity_id": entity_id, "value": value}))
        await self._run(calls)

    async def apply_speaker(self, body: dict[str, Any]) -> None:
        player = self.entity_id("media_player", "Speaker")
        calls: list[Call] = []
        if "volume" in body:
            calls.append(("media_player", "volume_set", {"entity_id": player, "volume_level": body["volume"]}))
        if "action" in body:
            service = {"play": "media_play", "pause": "media_pause", "stop": "media_stop"}[body["action"]]
            calls.append(("media_player", service, {"entity_id": player}))
        if "media_url" in body:
            calls.append(
                (
                    "media_player",
                    "play_media",
                    {"entity_id": player, "media_content_id": body["media_url"], "media_content_type": "music"},
                )
            )
        if "message" in body:
            calls.append(
                (
                    "tts",
                    "speak",
                    {"entity_id": body["tts_entity"], "media_player_entity_id": player, "message": body["message"]},
                )
            )
        await self._run(calls)

    async def apply_voice(self, body: dict[str, Any]) -> None:
        switch = self.entity_id("switch", "Wake Word Mode")
        service = "turn_on" if body["wake_word_mode"] else "turn_off"
        await self._run([("switch", service, {"entity_id": switch})])

    def state(self) -> dict[str, Any]:
        return {
            "display": self.display_state(),
            "speaker": self.speaker_state(),
            "voice": self.voice_state(),
            "touch": self.touch_state(),
        }

    def display_state(self) -> dict[str, Any]:
        return {field: self._read(*target) for field, target in DISPLAY_FIELDS.items()}

    def touch_state(self) -> dict[str, Any]:
        return {key: self._read(*target) for key, target in TOUCH_ENTITIES.items()}

    def speaker_state(self) -> dict[str, Any]:
        state = self._state("media_player", "Speaker")
        if state is None:
            return {"state": None, "volume": None}
        return {"state": state.state, "volume": state.attributes.get("volume_level")}

    def voice_state(self) -> dict[str, Any]:
        state = self._state("switch", "Wake Word Mode")
        return {"wake_word_mode": None if state is None else state.state == "on"}

    def _state(self, domain: str, name: str) -> State | None:
        try:
            return self._hass.states.get(self.entity_id(domain, name))
        except EntityNotFound:
            return None

    def _read(self, domain: str, name: str) -> Any:
        state = self._state(domain, name)
        if state is None or state.state in ("unavailable", "unknown"):
            return None
        if domain == "light":
            return {"on": state.state == "on", "rgb_color": state.attributes.get("rgb_color")}
        if domain == "event":
            return {"event_type": state.attributes.get("event_type"), "at": state.state}
        if domain == "binary_sensor":
            return state.state == "on"
        if domain == "number":
            return float(state.state)
        return state.state
