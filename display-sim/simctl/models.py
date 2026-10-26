"""The API's request and response models. Everything that crosses the HTTP boundary is typed here."""
from typing import Annotated

from pydantic import BaseModel, Field, StringConstraints, field_validator

from .meta import FPS_DEFAULT, FPS_MAX, FPS_MIN, FPS_STEP, Meta

HEX_PATTERN = r"^#[0-9a-f]{6}$"
HexColor = Annotated[str, StringConstraints(pattern=HEX_PATTERN)]


class Settings(BaseModel):
    expression: str
    voice: str = "Idle"
    speaking: bool = False
    accent: HexColor
    background: HexColor = "#000000"
    fps: int = Field(default=FPS_DEFAULT, ge=FPS_MIN, le=FPS_MAX)

    @field_validator("fps")
    @classmethod
    def _on_step(cls, fps: int) -> int:
        if (fps - FPS_MIN) % FPS_STEP:
            raise ValueError(f"fps must be {FPS_MIN} to {FPS_MAX} in steps of {FPS_STEP}")
        return fps


def option_problems(settings: Settings, meta: Meta) -> list[str]:
    """The values that are not an expression or voice the face knows; empty when they are fine."""
    found = []
    if settings.expression not in meta.expressions:
        found.append(f"unknown expression '{settings.expression}'")
    if settings.voice not in meta.voices:
        found.append(f"unknown voice '{settings.voice}'")
    return found


class ColorOut(BaseModel):
    name: str
    rgb: tuple[int, int, int]


class ThemeOut(BaseModel):
    name: str
    bg: tuple[int, int, int]
    accent: tuple[int, int, int]


class FpsRange(BaseModel):
    min: int = FPS_MIN
    max: int = FPS_MAX
    step: int = FPS_STEP
    default: int = FPS_DEFAULT


class MetaOut(BaseModel):
    """What can be set: expressions, voice states, colors, themes and the frame rate range."""

    expressions: list[str]
    voices: list[str]
    colors: list[ColorOut]
    themes: list[ThemeOut]
    fps: FpsRange

    @classmethod
    def from_meta(cls, meta: Meta) -> "MetaOut":
        return cls(
            expressions=meta.expressions,
            voices=meta.voices,
            colors=[ColorOut(name=c.name, rgb=c.rgb) for c in meta.colors],
            themes=[ThemeOut(name=t.name, bg=t.bg, accent=t.accent) for t in meta.themes],
            fps=FpsRange(),
        )


class RestartOut(BaseModel):
    status: str
