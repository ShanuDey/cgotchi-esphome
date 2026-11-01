"""Request schemas and ordering. No Home Assistant imports, so tests can load this file alone."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from .const import CLOCK_FORMATS, DISPLAY_FIELDS, EXPRESSIONS, PAGES, THEMES

def _number(value: Any) -> Any:
    """Numbers only: True and False are ints in Python but are not numbers in JSON."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise vol.Invalid("expected a number")
    return value


_BYTE = vol.All(_number, int, vol.Range(min=0, max=255))
_COLOR = vol.All([_BYTE], vol.Length(min=3, max=3))
_VOLUME = vol.All(_number, vol.Range(min=0, max=1))

DISPLAY_SCHEMA = vol.Schema(
    {
        vol.Optional("page"): vol.In(PAGES),
        vol.Optional("frame_source"): str,
        vol.Optional("frame_url"): vol.All(str, vol.Length(max=255)),
        vol.Optional("clock_format"): vol.In(CLOCK_FORMATS),
        vol.Optional("theme"): vol.In(THEMES),
        vol.Optional("expression"): vol.In(EXPRESSIONS),
        vol.Optional("frame_rate"): vol.All(_number, int, vol.Range(min=5, max=25)),
        vol.Optional("message_title"): vol.All(str, vol.Length(max=16)),
        vol.Optional("message_body"): vol.All(str, vol.Length(max=120)),
        vol.Optional("accent_color"): _COLOR,
        vol.Optional("secondary_color"): _COLOR,
        vol.Optional("background_color"): _COLOR,
    }
)


def _speaker_rules(body: dict[str, Any]) -> dict[str, Any]:
    if not body:
        raise vol.Invalid("send at least one field")
    if ("message" in body) != ("tts_entity" in body):
        raise vol.Invalid("message and tts_entity go together")
    return body


SPEAKER_SCHEMA = vol.All(
    vol.Schema(
        {
            vol.Optional("media_url"): str,
            vol.Optional("volume"): _VOLUME,
            vol.Optional("action"): vol.In(["play", "pause", "stop"]),
            vol.Optional("message"): str,
            vol.Optional("tts_entity"): str,
        }
    ),
    _speaker_rules,
)
VOICE_SCHEMA = vol.Schema({vol.Required("wake_word_mode"): bool})


def display_in_order(body: dict[str, Any]) -> list[tuple[str, Any]]:
    """Fields in the fixed DISPLAY_FIELDS order (theme before the colors), not the order the client sent."""
    return [(field, body[field]) for field in DISPLAY_FIELDS if field in body]
