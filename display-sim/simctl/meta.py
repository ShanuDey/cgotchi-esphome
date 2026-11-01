"""What the simulator can show, as plain data. face_headers.py fills it from the face component."""
from dataclasses import dataclass
from typing import NamedTuple

# Must match the "Face Frame Rate" number in display-sim.yaml.
FPS_MIN, FPS_MAX, FPS_STEP, FPS_DEFAULT = 5, 25, 5, 20

# Must match the "Display Page" select in display-sim.yaml (the device also has Display Frame, WebView).
PAGES = ["Face", "Clock", "Message"]

# Must match max_length of the Message Title and Message Body texts in cgotchi.yaml.
MESSAGE_TITLE_MAX, MESSAGE_BODY_MAX = 16, 120


class Rgb(NamedTuple):
    r: int
    g: int
    b: int

    @property
    def hex(self) -> str:
        return "#{:02x}{:02x}{:02x}".format(*self)


@dataclass(frozen=True)
class Theme:
    name: str
    bg: Rgb
    accent: Rgb
    secondary: Rgb


@dataclass(frozen=True)
class Meta:
    pages: list[str]
    expressions: list[str]
    voices: list[str]
    themes: list[Theme]
