"""The API's request and response models. Everything that crosses the HTTP boundary is typed here."""
import re
from typing import Annotated

from pydantic import BaseModel, Field, StringConstraints, field_validator

from .meta import FPS_DEFAULT, FPS_MAX, FPS_MIN, FPS_STEP, MESSAGE_BODY_MAX, MESSAGE_TITLE_MAX, Meta

HEX_PATTERN = r"^#[0-9a-f]{6}$"
HexColor = Annotated[str, StringConstraints(pattern=HEX_PATTERN)]
CLOCK_TIME = re.compile(r"^([01]\d|2[0-3]):[0-5]\d$")


class Settings(BaseModel):
    page: str = "Face"
    expression: str
    voice: str = "Idle"
    speaking: bool = False
    accent: HexColor
    secondary: HexColor
    background: HexColor = "#000000"
    fps: int = Field(default=FPS_DEFAULT, ge=FPS_MIN, le=FPS_MAX)
    clock_24h: bool = False
    clock_time: str = ""   # "HH:MM" freezes the clock; empty is the computer's time
    message_title: str = Field(default="Hello", max_length=MESSAGE_TITLE_MAX)
    message_body: str = Field(default="Set me from Home Assistant", max_length=MESSAGE_BODY_MAX)

    @field_validator("clock_time")
    @classmethod
    def _clock_time(cls, value: str) -> str:
        if value and not CLOCK_TIME.match(value):
            raise ValueError("clock_time must be empty or a time like 09:30")
        return value

    @field_validator("message_title", "message_body")
    @classmethod
    def _one_line(cls, value: str) -> str:
        if "\n" in value or "\r" in value:
            raise ValueError("message text must be one line")
        return value

    @field_validator("fps")
    @classmethod
    def _on_step(cls, fps: int) -> int:
        if (fps - FPS_MIN) % FPS_STEP:
            raise ValueError(f"fps must be {FPS_MIN} to {FPS_MAX} in steps of {FPS_STEP}")
        return fps


def option_problems(settings: Settings, meta: Meta) -> list[str]:
    """Values that are not a known page, expression or voice."""
    found = []
    if settings.page not in meta.pages:
        found.append(f"unknown page '{settings.page}'")
    if settings.expression not in meta.expressions:
        found.append(f"unknown expression '{settings.expression}'")
    if settings.voice not in meta.voices:
        found.append(f"unknown voice '{settings.voice}'")
    return found


class ThemeOut(BaseModel):
    name: str
    bg: tuple[int, int, int]
    accent: tuple[int, int, int]
    secondary: tuple[int, int, int]


class FpsRange(BaseModel):
    min: int = FPS_MIN
    max: int = FPS_MAX
    step: int = FPS_STEP
    default: int = FPS_DEFAULT


class MetaOut(BaseModel):
    """What can be set."""

    pages: list[str]
    expressions: list[str]
    voices: list[str]
    themes: list[ThemeOut]
    fps: FpsRange
    title_max: int = MESSAGE_TITLE_MAX
    body_max: int = MESSAGE_BODY_MAX

    @classmethod
    def from_meta(cls, meta: Meta) -> "MetaOut":
        return cls(
            pages=meta.pages,
            expressions=meta.expressions,
            voices=meta.voices,
            themes=[ThemeOut(name=t.name, bg=t.bg, accent=t.accent, secondary=t.secondary) for t in meta.themes],
            fps=FpsRange(),
        )


class RestartOut(BaseModel):
    status: str
