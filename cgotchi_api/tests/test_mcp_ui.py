import contextlib
import io
import unittest
from types import SimpleNamespace

from cgotchi_api import mcp_ui

ENV = {"CGOTCHI_HA_URL": "http://ha.example:8123/"}


class McpUiTests(unittest.TestCase):
    def launch(self, args=(), env=ENV, npx="/bin/npx"):
        calls = []

        def run(command):
            calls.append(command)
            return SimpleNamespace(returncode=3)

        code = mcp_ui.main(list(args), env=env, which=lambda _: npx, run=run)
        return code, calls

    def test_runs_the_pinned_inspector_and_passes_options_through(self) -> None:
        code, calls = self.launch(["--web"])
        self.assertEqual(code, 3)
        self.assertEqual(calls, [["/bin/npx", "-y", mcp_ui.INSPECTOR, "--web"]])
        self.assertRegex(mcp_ui.INSPECTOR, r"@\d+\.\d+\.\d+$")

    def test_help_prints_usage_and_does_not_launch(self) -> None:
        code, calls = self.launch(["--help"])
        self.assertEqual((code, calls), (0, []))

    def test_the_hint_never_prints_the_token(self) -> None:
        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            self.launch(env={**ENV, "CGOTCHI_HA_TOKEN": "s3cret"})
        self.assertNotIn("s3cret", err.getvalue())
        self.assertIn(mcp_ui.endpoint(ENV), err.getvalue())

    def test_endpoint_is_built_from_the_ha_url(self) -> None:
        self.assertEqual(mcp_ui.endpoint(ENV), "http://ha.example:8123/api/cgotchi/mcp")

    def test_missing_url_or_npx_stops_with_a_message(self) -> None:
        with self.assertRaises(SystemExit):
            self.launch(env={})
        with self.assertRaises(SystemExit):
            self.launch(npx=None)


if __name__ == "__main__":
    unittest.main()
