"""What the simulator can show, as plain data. face_headers.py fills it from the face component."""
from dataclasses import dataclass
from typing import NamedTuple

# Must match the "Face Frame Rate" number in display-sim.yaml.
FPS_MIN, FPS_MAX, FPS_STEP, FPS_DEFAULT = 5, 25, 5, 20


class Rgb(NamedTuple):
    r: int
    g: int
    b: int

    @property
    def hex(self) -> str:
        return "#{:02x}{:02x}{:02x}".format(*self)


@dataclass(frozen=True)
class Color:
    name: str
    rgb: Rgb

    @property
    def hex(self) -> str:
        return self.rgb.hex


@dataclass(frozen=True)
class Theme:
    name: str
    bg: Rgb
    accent: Rgb


@dataclass(frozen=True)
class Meta:
    expressions: list[str]
    voices: list[str]
    colors: list[Color]
    themes: list[Theme]
