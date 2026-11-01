"""Command line: cgotchi api <command>."""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any

from .api_client import ApiError, CgotchiClient
from .settings import ConfigError, load_settings

DISPLAY_FIELDS = [
    "page", "frame_source", "frame_url", "clock_format", "theme", "expression",
    "message_title", "message_body",
]
COLOR_FIELDS = ["accent_color", "secondary_color", "background_color"]


def _color(text: str) -> list[int]:
    parts = [int(p) for p in text.split(",")]
    if len(parts) != 3:
        raise argparse.ArgumentTypeError("use R,G,B, e.g. 0,200,255")
    return parts


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="cgotchi api", description="Drive cgotchi through Home Assistant.")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("state", help="show everything")
    sub.add_parser("touch", help="show touch, buttons and motion")

    display = sub.add_parser("display", help="change the display")
    for field in DISPLAY_FIELDS:
        display.add_argument(f"--{field.replace('_', '-')}", dest=field)
    display.add_argument("--frame-rate", type=int)
    for field in COLOR_FIELDS:
        display.add_argument(f"--{field.replace('_', '-')}", dest=field, type=_color, metavar="R,G,B")

    speaker = sub.add_parser("speaker", help="play audio, speak text or set the volume")
    speaker.add_argument("--media-url")
    speaker.add_argument("--volume", type=float)
    speaker.add_argument("--action", choices=["play", "pause", "stop"])
    speaker.add_argument("--message")
    speaker.add_argument("--tts-entity")

    wake = sub.add_parser("wake-word", help="turn the on-device wake word on or off")
    wake.add_argument("enabled", choices=["on", "off"])
    return parser


def _fields(args: argparse.Namespace, names: list[str]) -> dict[str, Any]:
    return {name: getattr(args, name) for name in names if getattr(args, name) is not None}


def run(args: argparse.Namespace, client: CgotchiClient) -> Any:
    if args.command == "state":
        return client.state()
    if args.command == "touch":
        return client.touch()
    if args.command == "display":
        fields = _fields(args, DISPLAY_FIELDS + COLOR_FIELDS + ["frame_rate"])
        return client.set_display(**fields) if fields else client.get_display()
    if args.command == "speaker":
        fields = _fields(args, ["media_url", "volume", "action", "message", "tts_entity"])
        return client.set_speaker(**fields) if fields else client.get_speaker()
    return client.set_wake_word(args.enabled == "on")


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        print(json.dumps(run(args, CgotchiClient(load_settings())), indent=2))
    except (ConfigError, ApiError) as err:
        print(err, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
