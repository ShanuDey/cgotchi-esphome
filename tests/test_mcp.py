"""Tests for the MCP protocol layer and its tools, built from the real openapi.yaml."""
import asyncio
import json
import unittest
from unittest.mock import AsyncMock, MagicMock

import yaml

from tests.test_integration import PACKAGE, load

mcp = load("mcp")
const = load("const")

SPEC = yaml.safe_load((PACKAGE / "openapi.yaml").read_text("utf-8"))
HTTP = ("get", "post", "put", "patch", "delete")


def run(coro):
    return asyncio.run(coro)


def rpc(method, params=None, id=1):
    message = {"jsonrpc": "2.0", "id": id, "method": method}
    if params is not None:
        message["params"] = params
    return message


class FakeDevice:
    def __init__(self):
        self.apply_display = AsyncMock()
        self.apply_speaker = AsyncMock()
        self.apply_voice = AsyncMock()
        self.display_state = MagicMock(return_value={"theme": "Night"})
        self.speaker_state = MagicMock(return_value={"state": "idle", "volume": 0.5})
        self.voice_state = MagicMock(return_value={"wake_word_mode": True})
        self.touch_state = MagicMock(return_value={"moving": False})
        self.state = MagicMock(return_value={"display": {}, "speaker": {}, "voice": {}, "touch": {}})


class ProtocolTests(unittest.TestCase):
    def setUp(self) -> None:
        self.server = mcp.McpServer(SPEC)
        self.device = FakeDevice()

    def handle(self, message, errors=()):
        return run(self.server.handle(self.device, message, errors))

    def test_initialize_echoes_a_supported_version_and_offers_tools(self) -> None:
        reply = self.handle(rpc("initialize", {"protocolVersion": "2025-03-26"}))
        result = reply["result"]
        self.assertEqual(result["protocolVersion"], "2025-03-26")
        self.assertIn("tools", result["capabilities"])
        self.assertEqual(result["serverInfo"]["version"], SPEC["info"]["version"])

    def test_initialize_falls_back_to_the_newest_supported_version(self) -> None:
        reply = self.handle(rpc("initialize", {"protocolVersion": "1999-01-01"}))
        self.assertEqual(reply["result"]["protocolVersion"], mcp.PROTOCOLS[0])

    def test_notifications_and_responses_get_no_reply(self) -> None:
        self.assertIsNone(self.handle({"jsonrpc": "2.0", "method": "notifications/initialized"}))
        self.assertIsNone(self.handle({"jsonrpc": "2.0", "id": 3, "result": {}}))

    def test_ping(self) -> None:
        self.assertEqual(self.handle(rpc("ping"))["result"], {})

    def test_unknown_method_and_bad_shapes_are_protocol_errors(self) -> None:
        self.assertEqual(self.handle(rpc("nope"))["error"]["code"], mcp.METHOD_NOT_FOUND)
        self.assertEqual(self.handle([rpc("ping")])["error"]["code"], mcp.INVALID_REQUEST)
        self.assertEqual(self.handle({"jsonrpc": "2.0", "id": 1})["error"]["code"], mcp.INVALID_REQUEST)
        self.assertEqual(self.handle(rpc("tools/list", params=[]))["error"]["code"], mcp.INVALID_PARAMS)
        self.assertEqual(self.handle({"jsonrpc": "2.0", "id": 1, "method": 5})["error"]["code"], mcp.INVALID_REQUEST)
        null_params = {"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": None}
        self.assertEqual(self.handle(null_params)["error"]["code"], mcp.INVALID_PARAMS)

    def test_reply_keeps_the_request_id(self) -> None:
        self.assertEqual(self.handle(rpc("ping", id="abc"))["id"], "abc")


class ToolListTests(unittest.TestCase):
    def setUp(self) -> None:
        listing = run(mcp.McpServer(SPEC).handle(None, rpc("tools/list")))
        self.tools = {tool["name"]: tool for tool in listing["result"]["tools"]}

    def test_one_tool_per_operation(self) -> None:
        self.assertEqual(set(self.tools), set(mcp.HANDLERS))
        operations = {
            op["operationId"] for item in SPEC["paths"].values() for method, op in item.items() if method in HTTP
        }
        self.assertEqual(set(self.tools), operations)

    def test_every_tool_has_a_description_and_an_object_schema(self) -> None:
        for name, tool in self.tools.items():
            with self.subTest(tool=name):
                self.assertTrue(tool["description"])
                self.assertEqual(tool["inputSchema"]["type"], "object")

    def test_refs_are_inlined(self) -> None:
        self.assertNotIn("$ref", json.dumps(list(self.tools.values())))
        colors = self.tools["set_display"]["inputSchema"]["properties"]["accent_color"]
        self.assertEqual((colors["minItems"], colors["maxItems"]), (3, 3))

    def test_read_tools_take_no_arguments(self) -> None:
        self.assertEqual(self.tools["get_state"]["inputSchema"], {"type": "object", "properties": {}})


class SpecMatchesCodeTests(unittest.TestCase):
    """The spec is advertised to agents, the voluptuous schemas validate: they must not drift apart."""

    def setUp(self) -> None:
        self.display = SPEC["components"]["schemas"]["DisplayRequest"]["properties"]

    def test_enums_match_the_constants(self) -> None:
        self.assertEqual(self.display["page"]["enum"], const.PAGES)
        self.assertEqual(self.display["theme"]["enum"], const.THEMES)
        self.assertEqual(self.display["expression"]["enum"], const.EXPRESSIONS)
        self.assertEqual(self.display["clock_format"]["enum"], const.CLOCK_FORMATS)

    def test_fields_match_the_display_fields(self) -> None:
        self.assertEqual(set(self.display), set(const.DISPLAY_FIELDS))

    def test_limits_match_the_schemas(self) -> None:
        self.assertEqual(self.display["message_title"]["maxLength"], 16)
        self.assertEqual(self.display["message_body"]["maxLength"], 120)
        self.assertEqual((self.display["frame_rate"]["minimum"], self.display["frame_rate"]["maximum"]), (5, 25))

    def test_a_missing_handler_or_operation_is_refused(self) -> None:
        spec = json.loads(json.dumps(SPEC))
        spec["paths"]["/api/cgotchi/touch"]["get"]["operationId"] = "unknown_tool"
        with self.assertRaises(ValueError):
            mcp.build_tools(spec)
        del spec["paths"]["/api/cgotchi/touch"]
        with self.assertRaises(ValueError):
            mcp.build_tools(spec)

    def test_path_and_query_parameters_are_refused(self) -> None:
        spec = json.loads(json.dumps(SPEC))
        spec["paths"]["/api/cgotchi/touch"]["get"]["parameters"] = [{"name": "x", "in": "query"}]
        with self.assertRaises(ValueError):
            mcp.build_tools(spec)


class ToolCallTests(unittest.TestCase):
    def setUp(self) -> None:
        self.server = mcp.McpServer(SPEC)
        self.device = FakeDevice()

    def call(self, name, arguments=None, errors=()):
        params = {"name": name}
        if arguments is not None:
            params["arguments"] = arguments
        return run(self.server.handle(self.device, rpc("tools/call", params), errors))

    def payload(self, reply):
        self.assertNotIn("isError", reply["result"])
        return json.loads(reply["result"]["content"][0]["text"])

    def test_read_tools_return_the_device_state(self) -> None:
        self.assertEqual(self.payload(self.call("get_display")), {"theme": "Night"})
        self.assertEqual(self.payload(self.call("get_speaker"))["volume"], 0.5)
        self.assertEqual(self.payload(self.call("get_wake_word")), {"wake_word_mode": True})
        self.assertEqual(self.payload(self.call("get_touch")), {"moving": False})
        self.assertEqual(set(self.payload(self.call("get_state"))), {"display", "speaker", "voice", "touch"})

    def test_set_display_applies_then_reads_back(self) -> None:
        reply = self.call("set_display", {"theme": "Night", "accent_color": [0, 200, 255]})
        self.assertEqual(self.payload(reply), {"theme": "Night"})
        self.device.apply_display.assert_awaited_once_with({"theme": "Night", "accent_color": [0, 200, 255]})

    def test_set_speaker_and_wake_word(self) -> None:
        self.call("set_speaker", {"volume": 0.5})
        self.device.apply_speaker.assert_awaited_once_with({"volume": 0.5})
        self.call("set_wake_word", {"wake_word_mode": False})
        self.device.apply_voice.assert_awaited_once_with({"wake_word_mode": False})

    def test_invalid_arguments_are_a_tool_error_and_nothing_is_applied(self) -> None:
        for name, arguments in (
            ("set_display", {"theme": "Neon"}),
            ("set_display", {"nope": 1}),
            ("set_speaker", {}),
            ("set_speaker", {"message": "hi"}),
            ("set_wake_word", {}),
        ):
            with self.subTest(name=name, arguments=arguments):
                result = self.call(name, arguments)["result"]
                self.assertTrue(result["isError"])
                self.assertIn("invalid arguments", result["content"][0]["text"])
        self.device.apply_display.assert_not_awaited()
        self.device.apply_speaker.assert_not_awaited()
        self.device.apply_voice.assert_not_awaited()

    def test_null_arguments_count_as_none_given(self) -> None:
        reply = run(self.server.handle(self.device, rpc("tools/call", {"name": "get_state", "arguments": None})))
        self.assertEqual(set(self.payload(reply)), {"display", "speaker", "voice", "touch"})

    def test_unserializable_state_is_still_returned(self) -> None:
        self.device.display_state.return_value = {"when": object}
        self.assertIn("when", self.payload(self.call("get_display")))

    def test_listed_device_errors_are_tool_errors(self) -> None:
        self.device.apply_display.side_effect = KeyError("entity")
        result = self.call("set_display", {"theme": "Night"}, errors=(KeyError,))["result"]
        self.assertTrue(result["isError"])

    def test_other_errors_are_an_internal_protocol_error(self) -> None:
        self.device.apply_display.side_effect = RuntimeError("boom")
        with self.assertLogs(level="ERROR"):
            reply = self.call("set_display", {"theme": "Night"})
        self.assertEqual(reply["error"]["code"], mcp.INTERNAL_ERROR)
        self.assertNotIn("boom", reply["error"]["message"])

    def test_unknown_tool_and_bad_arguments_are_protocol_errors(self) -> None:
        self.assertEqual(self.call("nope")["error"]["code"], mcp.INVALID_PARAMS)
        self.assertEqual(self.call(["x"])["error"]["code"], mcp.INVALID_PARAMS)
        self.assertEqual(self.call("get_state", ["x"])["error"]["code"], mcp.INVALID_PARAMS)


if __name__ == "__main__":
    unittest.main()
