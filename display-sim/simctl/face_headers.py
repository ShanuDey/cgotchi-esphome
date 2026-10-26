"""Reads what can be set from components/face/looks.h and components/display_ui/themes.h.

Reading the headers keeps one source of truth: add an expression or a color there and it appears
on the page after a restart. The parsing relies on the plain style those headers are written in.
"""
import re
from functools import lru_cache

from .config import FACE_DIR, UI_DIR
from .meta import PAGES, Meta, Rgb, Theme

NUMBER = r"-?\d+(?:\.\d+)?"


def _rgb(*parts: str) -> Rgb:
    return Rgb(*(round(float(p) * 255) for p in parts))


def parse_enum(text: str, name: str) -> list[str]:
    block = re.search(rf"enum class {name}[^{{]*\{{([^}}]*)\}}", text)
    if not block:
        raise RuntimeError(f"looks.h: enum {name} not found")
    return [n.strip() for n in block.group(1).split(",") if n.strip() and n.strip() != "Count"]


def parse_themes(text: str) -> list[Theme]:
    # {"Name", {r, g, b}, {r, g, b}, {r, g, b}}: background, accent, secondary
    triple = r"\{\s*(" + NUMBER + r")f,\s*(" + NUMBER + r")f,\s*(" + NUMBER + r")f\s*\}"
    pattern = r'\{"([\w ]+)",\s*' + triple + r",\s*" + triple + r",\s*" + triple + r"\}"
    themes = [Theme(m[0], _rgb(*m[1:4]), _rgb(*m[4:7]), _rgb(*m[7:10])) for m in re.findall(pattern, text)]
    if not themes:
        raise RuntimeError("themes.h: no themes found")
    return themes


@lru_cache
def load_meta() -> Meta:
    looks = (FACE_DIR / "looks.h").read_text(encoding="utf-8")
    colors = (UI_DIR / "themes.h").read_text(encoding="utf-8")
    return Meta(
        pages=list(PAGES),
        expressions=parse_enum(looks, "Expression"),
        voices=parse_enum(looks, "Voice"),
        themes=parse_themes(colors),
    )
