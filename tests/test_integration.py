"""Tests for the parts of custom_components/cgotchi that do not need Home Assistant."""
import importlib
import sys
import types
import unittest
from pathlib import Path

import voluptuous as vol

PACKAGE = Path(__file__).resolve().parent.parent / "custom_components" / "cgotchi"


def load(name: str):
    """Import a module of the integration without running its __init__ (which imports Home Assistant)."""
    if "cgotchi_pure" not in sys.modules:
        package = types.ModuleType("cgotchi_pure")
        package.__path__ = [str(PACKAGE)]
        sys.modules["cgotchi_pure"] = package
    return importlib.import_module(f"cgotchi_pure.{name}")


schemas = load("schemas")
const = load("const")


class DisplaySchemaTests(unittest.TestCase):
    def test_accepts_valid_fields(self) -> None:
        body = {"theme": "Night", "accent_color": [0, 200, 255], "frame_rate": 10}
        self.assertEqual(schemas.DISPLAY_SCHEMA(body), body)

    def test_rejects_unknown_theme_field_and_bad_color(self) -> None:
        for bad in ({"theme": "Neon"}, {"nope": 1}, {"accent_color": [0, 0]}, {"accent_color": [0, 0, 300]},
                    {"frame_rate": 99}, {"message_title": "x" * 17}):
            with self.subTest(bad=bad), self.assertRaises(vol.Invalid):
                schemas.DISPLAY_SCHEMA(bad)

    def test_theme_is_applied_before_colors(self) -> None:
        body = {"accent_color": [1, 2, 3], "page": "Face", "theme": "Night", "background_color": [0, 0, 0]}
        order = [field for field, _ in schemas.display_in_order(body)]
        self.assertLess(order.index("theme"), order.index("accent_color"))
        self.assertLess(order.index("theme"), order.index("background_color"))

    def test_every_display_field_has_a_schema_entry(self) -> None:
        keys = {str(key) for key in schemas.DISPLAY_SCHEMA.schema}
        self.assertEqual(keys, set(const.DISPLAY_FIELDS))


class SpeakerSchemaTests(unittest.TestCase):
    def test_volume_accepts_int_and_float_but_not_string(self) -> None:
        self.assertEqual(schemas.SPEAKER_SCHEMA({"volume": 1}), {"volume": 1})
        self.assertEqual(schemas.SPEAKER_SCHEMA({"volume": 0.5}), {"volume": 0.5})
        with self.assertRaises(vol.Invalid):
            schemas.SPEAKER_SCHEMA({"volume": "0.5"})

    def test_booleans_are_not_numbers(self) -> None:
        with self.assertRaises(vol.Invalid):
            schemas.SPEAKER_SCHEMA({"volume": True})
        for bad in ({"frame_rate": True}, {"accent_color": [True, 0, 0]}, {"frame_rate": 7.5}):
            with self.subTest(bad=bad), self.assertRaises(vol.Invalid):
                schemas.DISPLAY_SCHEMA(bad)

    def test_empty_body_and_lone_message_are_rejected(self) -> None:
        for bad in ({}, {"message": "hi"}, {"tts_entity": "tts.x"}):
            with self.subTest(bad=bad), self.assertRaises(vol.Invalid):
                schemas.SPEAKER_SCHEMA(bad)

    def test_message_with_tts_entity_is_accepted(self) -> None:
        body = {"message": "hi", "tts_entity": "tts.x"}
        self.assertEqual(schemas.SPEAKER_SCHEMA(body), body)


class SpecTests(unittest.TestCase):
    def test_every_key_is_a_string(self) -> None:
        """YAML turns an unquoted `on` or `no` key into a boolean, which breaks JSON output."""
        import yaml

        spec = yaml.safe_load((PACKAGE / "openapi.yaml").read_text("utf-8"))
        bad: list[str] = []

        def walk(node, path: str = "") -> None:
            if isinstance(node, dict):
                for key, value in node.items():
                    if not isinstance(key, str):
                        bad.append(f"{path}/{key!r}")
                    walk(value, f"{path}/{key}")
            elif isinstance(node, list):
                for index, value in enumerate(node):
                    walk(value, f"{path}[{index}]")

        walk(spec)
        self.assertEqual(bad, [])

    def test_spec_and_manifest_versions_match(self) -> None:
        import json

        import yaml

        spec = yaml.safe_load((PACKAGE / "openapi.yaml").read_text("utf-8"))
        manifest = json.loads((PACKAGE / "manifest.json").read_text("utf-8"))
        self.assertEqual(spec["info"]["version"], manifest["version"])

    def test_light_schema_names_its_on_field(self) -> None:
        import yaml

        spec = yaml.safe_load((PACKAGE / "openapi.yaml").read_text("utf-8"))
        self.assertIn("on", spec["components"]["schemas"]["Light"]["properties"])


class VoiceSchemaTests(unittest.TestCase):
    def test_requires_a_boolean(self) -> None:
        self.assertEqual(schemas.VOICE_SCHEMA({"wake_word_mode": True}), {"wake_word_mode": True})
        with self.assertRaises(vol.Invalid):
            schemas.VOICE_SCHEMA({"wake_word_mode": "on"})
        with self.assertRaises(vol.Invalid):
            schemas.VOICE_SCHEMA({})


if __name__ == "__main__":
    unittest.main()
