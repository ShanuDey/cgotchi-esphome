"""Copy the HA integration into a Home Assistant config folder, optionally restart HA.

    uv run cgotchi deploy api [--restart]

Reads CGOTCHI_DEPLOY_DIR (the HA config folder, e.g. \\\\homeassistant.local\\config) from the environment or
the repo-root .env; --restart also needs CGOTCHI_HA_URL and CGOTCHI_HA_TOKEN.
"""
import argparse
import shutil
import sys
import urllib.error
import urllib.request
from pathlib import Path

from .settings import read_env

SOURCE = Path(__file__).resolve().parent.parent / "custom_components" / "cgotchi"


def copy_tree(src: Path, dest: Path) -> None:
    """Files only, no permissions or timestamps: a share can reject them."""
    dest.mkdir(parents=True)
    for item in src.rglob("*"):
        if "__pycache__" in item.parts:
            continue
        target = dest / item.relative_to(src)
        if item.is_dir():
            target.mkdir()
        else:
            shutil.copyfile(item, target)


def copy_integration(config_dir: Path) -> Path:
    """Copies next to the live folder and swaps, so a failed copy never leaves HA without the integration."""
    parent = config_dir / "custom_components"
    dest, staging, old = parent / "cgotchi", parent / ".cgotchi.new", parent / ".cgotchi.old"
    if dest.resolve() == SOURCE.resolve():
        sys.exit("CGOTCHI_DEPLOY_DIR is this repo; point it at the Home Assistant config folder")
    for leftover in (staging, old):
        shutil.rmtree(leftover, ignore_errors=True)
    try:
        copy_tree(SOURCE, staging)
        had_old = dest.exists()
        if had_old:
            dest.rename(old)
        try:
            staging.rename(dest)
        except OSError:
            if had_old:
                old.rename(dest)   # put the working copy back
            raise
    finally:
        shutil.rmtree(staging, ignore_errors=True)
    shutil.rmtree(old, ignore_errors=True)
    return dest


def restart_home_assistant(env: dict[str, str]) -> None:
    url, token = env.get("CGOTCHI_HA_URL", ""), env.get("CGOTCHI_HA_TOKEN", "")
    if not url or not token:
        sys.exit("--restart needs CGOTCHI_HA_URL and CGOTCHI_HA_TOKEN (see .env.example)")
    request = urllib.request.Request(
        f"{url.rstrip('/')}/api/services/homeassistant/restart",
        data=b"{}",
        method="POST",
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
    )
    try:
        urllib.request.urlopen(request, timeout=15).close()
    except urllib.error.HTTPError as err:
        sys.exit(f"restart failed: HTTP {err.code} (check CGOTCHI_HA_TOKEN)")
    except (TimeoutError, ConnectionResetError):
        pass   # HA goes down before it answers
    except urllib.error.URLError as err:
        if not isinstance(err.reason, (TimeoutError, ConnectionResetError)):
            sys.exit(f"restart failed: {err}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="cgotchi deploy api", description=__doc__.splitlines()[0])
    parser.add_argument("--restart", action="store_true", help="restart Home Assistant after copying")
    args = parser.parse_args(argv)
    env = read_env()
    target = env.get("CGOTCHI_DEPLOY_DIR")
    if not target:
        sys.exit("set CGOTCHI_DEPLOY_DIR to the Home Assistant config folder (see .env.example)")
    try:
        print(f"copied to {copy_integration(Path(target))}")
    except OSError as err:
        sys.exit(f"copy failed: {err}\nCheck the share login and the permissions of custom_components/cgotchi on the HA side.")
    if args.restart:
        restart_home_assistant(env)
        print("restart requested")
    return 0
