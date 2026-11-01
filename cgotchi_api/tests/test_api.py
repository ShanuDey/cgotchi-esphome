import json
import tempfile
import unittest
import urllib.request
from pathlib import Path
from unittest.mock import patch

from cgotchi_api.api_client import ApiError, CgotchiClient
from cgotchi_api.settings import ConfigError, Settings, load_settings, parse_env_file
from cgotchi_api import deploy
from cgotchi_api.cli import build_parser, run


class FakeTransport:
    def __init__(self, status: int = 200, payload: bytes | dict | None = None) -> None:
        self.status = status
        self.payload = payload if isinstance(payload, bytes) else json.dumps(payload or {}).encode()
        self.requests: list[urllib.request.Request] = []

    def __call__(self, request: urllib.request.Request) -> tuple[int, bytes]:
        self.requests.append(request)
        return self.status, self.payload


def make_client(transport: FakeTransport) -> CgotchiClient:
    return CgotchiClient(Settings(url="http://ha:8123", token="tok"), transport)


class ConfigTests(unittest.TestCase):
    def test_environment_overrides_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / ".env"
            path.write_text('CGOTCHI_HA_URL="http://a/"\nCGOTCHI_HA_TOKEN=file\n# comment\n')
            settings = load_settings(path, {"CGOTCHI_HA_TOKEN": "env"})
        self.assertEqual(settings, Settings(url="http://a", token="env"))

    def test_inline_comment_is_dropped_but_quoted_hash_is_kept(self) -> None:
        values = parse_env_file("A=one # note\nB=\"two # kept\"\nC=\n")
        self.assertEqual(values, {"A": "one", "B": "two # kept", "C": ""})

    def test_missing_values_fail(self) -> None:
        with self.assertRaises(ConfigError):
            load_settings(None, {})


class ClientTests(unittest.TestCase):
    def test_sends_bearer_token_and_json(self) -> None:
        transport = FakeTransport(payload={"page": "Clock"})
        result = make_client(transport).set_display(page="Clock")
        request = transport.requests[0]
        self.assertEqual(result, {"page": "Clock"})
        self.assertEqual(request.full_url, "http://ha:8123/api/cgotchi/display")
        self.assertEqual(request.get_header("Authorization"), "Bearer tok")
        self.assertEqual(json.loads(request.data), {"page": "Clock"})

    def test_error_status_raises_with_message(self) -> None:
        with self.assertRaises(ApiError) as ctx:
            make_client(FakeTransport(400, {"message": "bad page"})).set_display(page="x")
        self.assertEqual(ctx.exception.status, 400)
        self.assertIn("bad page", str(ctx.exception))

    def test_non_json_reply_raises(self) -> None:
        with self.assertRaises(ApiError):
            make_client(FakeTransport(200, b"<html>login</html>")).state()


class DeployTests(unittest.TestCase):
    def test_copy_replaces_old_folder_and_skips_pycache(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            config = Path(tmp)
            old = config / "custom_components" / "cgotchi"
            old.mkdir(parents=True)
            (old / "stale.py").write_text("old")
            dest = deploy.copy_integration(config)
            names = {p.name for p in dest.rglob("*")}
            self.assertIn("manifest.json", names)
            self.assertNotIn("stale.py", names)
            self.assertNotIn("__pycache__", names)
            self.assertEqual([p.name for p in dest.parent.iterdir()], ["cgotchi"])

    def test_failed_swap_puts_the_old_folder_back(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            old = Path(tmp) / "custom_components" / "cgotchi"
            old.mkdir(parents=True)
            (old / "keep.py").write_text("old")
            real_rename = Path.rename

            def flaky(path, target):
                if path.name == ".cgotchi.new":
                    raise OSError("the share said no")
                return real_rename(path, target)

            with patch.object(Path, "rename", flaky), self.assertRaises(OSError):
                deploy.copy_integration(Path(tmp))
            self.assertEqual((old / "keep.py").read_text(), "old")
            self.assertEqual([p.name for p in old.parent.iterdir()], ["cgotchi"])

    def test_refuses_to_overwrite_the_source(self) -> None:
        with self.assertRaises(SystemExit):
            deploy.copy_integration(deploy.SOURCE.parent.parent)


class CliTests(unittest.TestCase):
    def test_display_flags_become_fields(self) -> None:
        transport = FakeTransport()
        args = build_parser().parse_args(["display", "--theme", "Night", "--accent-color", "0,200,255", "--frame-rate", "10"])
        run(args, make_client(transport))
        self.assertEqual(
            json.loads(transport.requests[0].data),
            {"theme": "Night", "accent_color": [0, 200, 255], "frame_rate": 10},
        )

    def test_display_without_flags_reads(self) -> None:
        transport = FakeTransport()
        run(build_parser().parse_args(["display"]), make_client(transport))
        self.assertEqual(transport.requests[0].get_method(), "GET")


if __name__ == "__main__":
    unittest.main()
