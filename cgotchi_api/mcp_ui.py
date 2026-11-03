"""Open the MCP Inspector web UI for the cgotchi MCP endpoint.

    uv run cgotchi mcp ui [inspector options]

Needs Node (npx). Reads CGOTCHI_HA_URL from the environment or the repo-root .env.
"""
from __future__ import annotations

import shutil
import subprocess
import sys
from typing import Callable

from .settings import read_env

INSPECTOR = "@modelcontextprotocol/inspector@2.13.0"


def endpoint(env: dict[str, str]) -> str:
    base = env.get("CGOTCHI_HA_URL", "").rstrip("/")
    if not base:
        raise SystemExit("set CGOTCHI_HA_URL (environment or .env, see .env.example)")
    return f"{base}/api/cgotchi/mcp"


def main(
    argv: list[str] | None = None,
    env: dict[str, str] | None = None,
    which: Callable[[str], str | None] = shutil.which,
    run: Callable[..., subprocess.CompletedProcess] = subprocess.run,
) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if args[:1] in (["-h"], ["--help"]):
        print(__doc__, file=sys.stderr)
        return 0
    npx = which("npx")
    if npx is None:
        raise SystemExit("npx not found: install Node.js to use the MCP Inspector")
    url = endpoint(read_env() if env is None else env)
    print(
        "In the Inspector choose transport Streamable HTTP, then enter:\n"
        f"  URL            {url}\n"
        "  Authorization  Bearer <CGOTCHI_HA_TOKEN from .env>\n"
        "The first run downloads the Inspector. Press Ctrl+C to stop.",
        file=sys.stderr,
    )
    return run([npx, "-y", INSPECTOR, *args]).returncode
