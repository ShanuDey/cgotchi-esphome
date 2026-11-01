"""Settings from the environment or the repo's .env file."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

ENV_FILE = Path(__file__).resolve().parents[1] / ".env"


class ConfigError(Exception):
    pass


@dataclass(frozen=True)
class Settings:
    url: str
    token: str


def parse_env_file(text: str) -> dict[str, str]:
    values: dict[str, str] = {}
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        value = value.strip()
        if len(value) > 1 and value[0] in "\"'" and value[-1] == value[0]:
            value = value[1:-1]
        else:
            value = value.split(" #", 1)[0].strip()
        values[key.strip()] = value
    return values


def read_env(env_file: Path | None = ENV_FILE, environ: dict[str, str] | None = None) -> dict[str, str]:
    """CGOTCHI_* values; real environment variables win over the .env file."""
    environ = dict(os.environ) if environ is None else environ
    file_values = parse_env_file(env_file.read_text("utf-8")) if env_file and env_file.is_file() else {}
    return {**file_values, **{k: v for k, v in environ.items() if k.startswith("CGOTCHI_")}}


def load_settings(env_file: Path | None = ENV_FILE, environ: dict[str, str] | None = None) -> Settings:
    merged = read_env(env_file, environ)
    url, token = merged.get("CGOTCHI_HA_URL", ""), merged.get("CGOTCHI_HA_TOKEN", "")
    if not url or not token:
        raise ConfigError("set CGOTCHI_HA_URL and CGOTCHI_HA_TOKEN (environment or .env, see .env.example)")
    return Settings(url=url.rstrip("/"), token=token)
