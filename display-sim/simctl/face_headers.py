"""Reads what can be set from components/face/looks.h and colors.h.

Reading the headers keeps one source of truth: add an expression or a color there and it appears
on the page after a restart. The parsing relies on the plain style those headers are written in.
"""
import re
from functools import lru_cache

from .config import FACE_DIR
from .meta import Color, Meta, Rgb, Theme

NUMBER = r"-?\d+(?:\.\d+)?"


def _rgb(*parts: str) -> Rgb:
    return Rgb(*(round(float(p) * 255) for p in parts))


def parse_enum(text: str, name: str) -> list[str]:
    block = re.search(rf"enum class {name}[^{{]*\{{([^}}]*)\}}", text)
    if not block:
        raise RuntimeError(f"looks.h: enum {name} not found")
    return [n.strip() for n in block.group(1).split(",") if n.strip() and n.strip() != "Count"]


def parse_colors(text: str) -> list[Color]:
    colors = [
        Color(name, _rgb(r, g, b))
        for name, r, g, b in re.findall(rf'\{{"(\w+)",\s*({NUMBER})f,\s*({NUMBER})f,\s*({NUMBER})f\}}', text)
    ]
    if not colors:
        raise RuntimeError("colors.h: no color presets found")
    return colors


def parse_themes(text: str) -> list[Theme]:
    # {"Name", {r, g, b}, {r, g, b}, {r, g, b}}: background, accent, secondary
    triple = r"\{\s*(" + NUMBER + r")f,\s*(" + NUMBER + r")f,\s*(" + NUMBER + r")f\s*\}"
    pattern = r'\{"([\w ]+)",\s*' + triple + r",\s*" + triple + r",\s*" + triple + r"\}"
    return [Theme(m[0], _rgb(*m[1:4]), _rgb(*m[4:7])) for m in re.findall(pattern, text)]


@lru_cache
def load_meta() -> Meta:
    looks = (FACE_DIR / "looks.h").read_text(encoding="utf-8")
    colors = (FACE_DIR / "colors.h").read_text(encoding="utf-8")
    return Meta(
        expressions=parse_enum(looks, "Expression"),
        voices=parse_enum(looks, "Voice"),
        colors=parse_colors(colors),
        themes=parse_themes(colors),
    )
