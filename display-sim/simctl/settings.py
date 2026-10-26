"""The settings model and the settings.txt file the simulator polls.

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

from pydantic import BaseModel

from . import SETTINGS_EXAMPLE_PATH, SETTINGS_PATH
from .meta import FPS_DEFAULT, FPS_MAX, FPS_MIN, FPS_STEP, Meta

HEADER = "# Written by control.py. Edit freely: the simulator applies saved changes.\n"
COMMENT = re.compile(r"\s#.*$")   # a comment starts at "#" after a space; a value may itself start with "#" (colors)
HEX = re.compile(r"^#[0-9a-f]{6}$")
ON = {"on", "true", "1"}
OFF = {"off", "false", "0"}


class Settings(BaseModel):
    expression: str
    voice: str = "Idle"
    speaking: bool = False
    accent: str
    background: str = "#000000"
    fps: int = FPS_DEFAULT

    def problems(self, meta: Meta) -> list[str]:
        """What is wrong with these values; empty when they are fine."""
        found = []
        if self.expression not in meta.expressions:
            found.append(f"unknown expression '{self.expression}'")
        if self.voice not in meta.voices:
            found.append(f"unknown voice '{self.voice}'")
        for key in ("accent", "background"):
            if not HEX.match(getattr(self, key)):
                found.append(f"{key} must be a color like #00c7ff")
        if not FPS_MIN <= self.fps <= FPS_MAX or (self.fps - FPS_MIN) % FPS_STEP:
            found.append(f"fps must be {FPS_MIN} to {FPS_MAX} in steps of {FPS_STEP}")
        return found

    def render(self) -> str:
        lines = [
            f"expression = {self.expression}",
            f"voice = {self.voice}",
            f"speaking = {'on' if self.speaking else 'off'}",
            f"accent = {self.accent}",
            f"background = {self.background}",
            f"fps = {self.fps}",
        ]
        return HEADER + "\n".join(lines) + "\n"


def parse(text: str, meta: Meta) -> Settings:
    """Reads settings.txt text. Anything unusable keeps its default."""
    settings = Settings(expression=meta.expressions[0], accent=meta.colors[0].hex)
    options = {
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
        value = (value[:1] + COMMENT.sub("", value[1:])).strip()   # keep a leading "#": it is a color, not a comment
        key, low = key.lower(), value.lower()
        try:
            if key in options:
                match = next((o for o in options[key] if o.lower() == low), None)
                if match:
                    setattr(settings, key, match)
            elif key in ("accent", "background"):
                if HEX.match(low):
                    setattr(settings, key, low)
            elif key == "speaking":
                if low in ON | OFF:
                    settings.speaking = low in ON
            elif key == "fps":
                settings.fps = int(float(value))
        except ValueError:
            continue
    return settings


class SettingsFile:
    def __init__(self, meta: Meta, path: Path = SETTINGS_PATH):
        self.meta = meta
        self.path = path

    def read(self) -> Settings:
        if not self.path.exists():
            shutil.copy(SETTINGS_EXAMPLE_PATH, self.path)
        return parse(self.path.read_text(encoding="utf-8"), self.meta)

    def write(self, settings: Settings) -> None:
        tmp = self.path.with_suffix(".tmp")
        tmp.write_text(settings.render(), encoding="utf-8", newline="\n")
        for attempt in range(5):   # the simulator (in WSL) may have the file open for a moment
            try:
                os.replace(tmp, self.path)
                return
            except PermissionError:
                if attempt == 4:
                    raise
                time.sleep(0.05)
