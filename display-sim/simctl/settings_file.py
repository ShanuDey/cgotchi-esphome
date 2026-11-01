"""The settings.txt file the simulator polls.

The file stands in for Home Assistant: it holds the same entities HA sets on the device. It is the
whole state, so the simulator resets whatever it does not mention. This module reads hand-edited
files leniently (bad lines are skipped, option names are case insensitive) and writes atomically so
the simulator never sees half a file.
"""
import os
import re
import shutil
import time
from pathlib import Path

from .config import SETTINGS_EXAMPLE_PATH, SETTINGS_PATH
from .meta import FPS_MAX, FPS_MIN, FPS_STEP, MESSAGE_BODY_MAX, MESSAGE_TITLE_MAX, Meta
from .models import CLOCK_TIME, HEX_PATTERN, Settings

HEADER = "# Written by control.py. Edit freely: the simulator applies saved changes.\n"
COMMENT = re.compile(r"\s#.*$")   # a comment starts at "#" after a space; a value may itself start with "#" (colors)
HEX = re.compile(HEX_PATTERN)
TEXTS = {"message_title": MESSAGE_TITLE_MAX, "message_body": MESSAGE_BODY_MAX}   # key: longest value
ON = {"on", "true", "1"}
OFF = {"off", "false", "0"}


def _on_off(value: bool) -> str:
    return "on" if value else "off"


def render(settings: Settings) -> str:
    lines = [
        f"page = {settings.page}",
        f"expression = {settings.expression}",
        f"voice = {settings.voice}",
        f"speaking = {_on_off(settings.speaking)}",
        f"accent = {settings.accent}",
        f"secondary = {settings.secondary}",
        f"background = {settings.background}",
        f"fps = {settings.fps}",
        f"clock_24h = {_on_off(settings.clock_24h)}",
        f"clock_time = {settings.clock_time}",
        f"message_title = {settings.message_title}",
        f"message_body = {settings.message_body}",
    ]
    return HEADER + "\n".join(lines) + "\n"


def parse(text: str, meta: Meta) -> Settings:
    """Reads settings.txt text. Anything unusable keeps its default."""
    theme = meta.themes[0]
    settings = Settings(expression=meta.expressions[0], accent=theme.accent.hex, secondary=theme.secondary.hex)
    options = {
        "page": meta.pages,
        "expression": meta.expressions,
        "voice": meta.voices,
    }
    for raw in text.splitlines():
        line = raw.strip()
        if line.startswith("#"):
            continue
        key, sep, value = (part.strip() for part in line.partition("="))
        if not sep:
            continue
        key = key.lower()
        if key in TEXTS:   # literal text: a "#" in it is not a comment
            setattr(settings, key, value[:TEXTS[key]])
            continue
        value = (value[:1] + COMMENT.sub("", value[1:])).strip()   # keep a leading "#": it is a color, not a comment
        low = value.lower()
        try:
            if key in options:
                match = next((o for o in options[key] if o.lower() == low), None)
                if match:
                    setattr(settings, key, match)
            elif key in ("accent", "secondary", "background"):
                if HEX.match(low):
                    setattr(settings, key, low)
            elif key in ("speaking", "clock_24h"):
                if low in ON | OFF:
                    setattr(settings, key, low in ON)
            elif key == "clock_time":
                if not value or CLOCK_TIME.match(value):
                    settings.clock_time = value
            elif key == "fps":
                fps = int(float(value))
                if FPS_MIN <= fps <= FPS_MAX and (fps - FPS_MIN) % FPS_STEP == 0:
                    settings.fps = fps
        except ValueError:
            continue
    return settings


class SettingsFile:
    def __init__(self, meta: Meta, path: Path = SETTINGS_PATH, example: Path = SETTINGS_EXAMPLE_PATH):
        self.meta = meta
        self.path = path
        self.example = example

    def ensure(self) -> None:
        """Creates the file from the example if it is missing, so the simulator finds it."""
        if not self.path.exists():
            shutil.copy(self.example, self.path)

    def read(self) -> Settings:
        source = self.path if self.path.exists() else self.example
        return parse(source.read_text(encoding="utf-8"), self.meta)

    def write(self, settings: Settings) -> None:
        tmp = self.path.with_suffix(".tmp")
        tmp.write_text(render(settings), encoding="utf-8", newline="\n")
        for attempt in range(5):   # the simulator (in WSL) may have the file open for a moment
            try:
                os.replace(tmp, self.path)
                return
            except PermissionError:
                if attempt == 4:
                    raise
                time.sleep(0.05)
