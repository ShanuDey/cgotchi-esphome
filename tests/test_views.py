"""Tests for the HTTP views' own logic (auth, error mapping, body checks) with stand-ins for Home Assistant."""
import asyncio
import sys
import types
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

from tests.test_integration import load


class StubView:
    """Stands in for HomeAssistantView: replies become tuples the tests can read."""

    def json(self, data, status_code=200):
        return ("json", status_code, data)

    def json_message(self, message, status_code=200):
        return ("message", status_code, message)


class StubResponse:
    def __init__(self, status=200, **_):
        self.status = status


def _install_stubs() -> list[str]:
    class HomeAssistantError(Exception):
        pass

    class ServiceValidationError(HomeAssistantError):
        pass

    class ServiceNotFound(ServiceValidationError):
        pass

    def module(name: str, **attrs) -> types.ModuleType:
        mod = types.ModuleType(name)
        mod.__dict__.update(attrs)
        sys.modules[name] = mod
        return mod

    names = {
        "aiohttp": dict(web=types.SimpleNamespace(Request=object, Response=StubResponse)),
        "homeassistant": {},
        "homeassistant.components": {},
        "homeassistant.components.http": dict(HomeAssistantView=StubView),
        "homeassistant.core": dict(HomeAssistant=object, State=object),
        "homeassistant.helpers": {},
        "homeassistant.helpers.entity_registry": {},
        "homeassistant.exceptions": dict(HomeAssistantError=HomeAssistantError,
                                         ServiceValidationError=ServiceValidationError,
                                         ServiceNotFound=ServiceNotFound),
    }
    created = [name for name in names if name not in sys.modules]
    for name in created:
        module(name, **names[name])
    sys.modules["homeassistant.helpers"].entity_registry = sys.modules["homeassistant.helpers.entity_registry"]
    return created


_created = _install_stubs()
views = load("views")
device_module = load("device")
errors = sys.modules["homeassistant.exceptions"]


def tearDownModule() -> None:
    for name in _created:
        sys.modules.pop(name, None)


class FakeHass:
    def __init__(self, data):
        self.data = data

    async def async_add_executor_job(self, job):
        return job()


class FakeRequest(dict):
    host = "ha.local:8123"

    def __init__(self, user, device, body=None, headers=None):
        super().__init__(hass_user=user)
        self.headers = headers or {}
        self.app = {"hass": FakeHass({"cgotchi": device} if device else {})}
        self._body = body

    async def json(self):
        if isinstance(self._body, Exception):
            raise self._body
        return self._body


ADMIN = types.SimpleNamespace(is_admin=True)
USER = types.SimpleNamespace(is_admin=False)


def run(coro):
    return asyncio.run(coro)


class AuthAndSetupTests(unittest.TestCase):
    def setUp(self) -> None:
        self.device = device_module.CgotchiDevice(None, "id")
        self.view = views.StateView()

    def get(self, user, device):
        with patch.object(device_module.CgotchiDevice, "display_state", return_value={}), \
             patch.object(device_module.CgotchiDevice, "speaker_state", return_value={}), \
             patch.object(device_module.CgotchiDevice, "voice_state", return_value={}), \
             patch.object(device_module.CgotchiDevice, "touch_state", return_value={}):
            return run(self.view.get(FakeRequest(user, device)))

    def test_non_admin_and_anonymous_get_403(self) -> None:
        self.assertEqual(self.get(USER, self.device)[1], 403)
        self.assertEqual(self.get(None, self.device)[1], 403)

    def test_admin_without_a_device_gets_503(self) -> None:
        self.assertEqual(self.get(ADMIN, None)[1], 503)

    def test_admin_gets_the_snapshot(self) -> None:
        kind, status, data = self.get(ADMIN, self.device)
        self.assertEqual((kind, status), ("json", 200))
        self.assertEqual(set(data), {"display", "speaker", "voice", "touch"})


class ErrorMappingTests(unittest.TestCase):
    def post(self, body, failure=None):
        device = device_module.CgotchiDevice(None, "id")
        apply = AsyncMock(side_effect=failure)
        with patch.object(device_module.CgotchiDevice, "apply_display", apply), \
             patch.object(device_module.CgotchiDevice, "display_state", return_value={"theme": "Night"}):
            reply = run(views.DisplayView().post(FakeRequest(ADMIN, device, body)))
        return reply, apply

    def test_valid_body_is_applied_and_state_returned(self) -> None:
        reply, apply = self.post({"theme": "Night"})
        self.assertEqual(reply, ("json", 200, {"theme": "Night"}))
        apply.assert_awaited_once()

    def test_invalid_or_unreadable_body_is_400_and_nothing_is_applied(self) -> None:
        for body in ({"theme": "Neon"}, {"nope": 1}, ValueError("not json")):
            with self.subTest(body=body):
                reply, apply = self.post(body)
                self.assertEqual(reply[1], 400)
                apply.assert_not_awaited()

    def test_missing_entity_and_missing_service_are_404(self) -> None:
        self.assertEqual(self.post({"theme": "Night"}, device_module.EntityNotFound("x"))[0][1], 404)
        self.assertEqual(self.post({"theme": "Night"}, errors.ServiceNotFound("tts"))[0][1], 404)

    def test_rejected_values_are_400_and_other_ha_errors_are_502(self) -> None:
        self.assertEqual(self.post({"theme": "Night"}, errors.ServiceValidationError("bad"))[0][1], 400)
        self.assertEqual(self.post({"theme": "Night"}, errors.HomeAssistantError("down"))[0][1], 502)


class McpViewTests(unittest.TestCase):
    def post(self, user, device, body):
        return run(views.McpView().post(FakeRequest(user, device, body)))

    def setUp(self) -> None:
        self.device = device_module.CgotchiDevice(None, "id")

    def test_non_admin_gets_403_and_no_device_gets_503(self) -> None:
        ping = {"jsonrpc": "2.0", "id": 1, "method": "ping"}
        self.assertEqual(self.post(USER, self.device, ping)[1], 403)
        self.assertEqual(self.post(None, self.device, ping)[1], 403)
        self.assertEqual(self.post(ADMIN, None, ping)[1], 503)

    def test_admin_gets_a_json_rpc_reply(self) -> None:
        kind, status, data = self.post(ADMIN, self.device, {"jsonrpc": "2.0", "id": 7, "method": "ping"})
        self.assertEqual((kind, status), ("json", 200))
        self.assertEqual(data, {"jsonrpc": "2.0", "id": 7, "result": {}})

    def test_notification_is_202_without_a_body(self) -> None:
        reply = self.post(ADMIN, self.device, {"jsonrpc": "2.0", "method": "notifications/initialized"})
        self.assertEqual(reply.status, 202)

    def test_unreadable_body_is_a_parse_error(self) -> None:
        reply = self.post(ADMIN, self.device, ValueError("not json"))
        self.assertEqual(reply[2]["error"]["code"], -32700)

    def test_missing_entity_is_a_tool_error_not_an_http_error(self) -> None:
        call = {"jsonrpc": "2.0", "id": 1, "method": "tools/call",
                "params": {"name": "set_display", "arguments": {"theme": "Night"}}}
        for failure in (device_module.EntityNotFound("x"), errors.HomeAssistantError("down")):
            apply = AsyncMock(side_effect=failure)
            with self.subTest(failure=type(failure).__name__):
                with patch.object(device_module.CgotchiDevice, "apply_display", apply):
                    kind, status, data = self.post(ADMIN, self.device, call)
                self.assertEqual((kind, status), ("json", 200))
                self.assertTrue(data["result"]["isError"])

    def test_a_foreign_origin_is_refused_and_same_or_no_origin_is_allowed(self) -> None:
        ping = {"jsonrpc": "2.0", "id": 1, "method": "ping"}
        for origin, allowed in (("http://evil.example", False), ("http://ha.local:8123", True), (None, True)):
            with self.subTest(origin=origin):
                headers = {"Origin": origin} if origin else {}
                reply = run(views.McpView().post(FakeRequest(ADMIN, self.device, ping, headers)))
                self.assertEqual(reply[1] == 200, allowed)
                if not allowed:
                    self.assertEqual(reply[1], 403)

    def test_only_post_is_defined_so_other_methods_get_405(self) -> None:
        self.assertTrue(hasattr(views.McpView, "post"))
        for method in ("get", "put", "delete", "patch"):
            self.assertFalse(hasattr(views.McpView, method), method)


class SpecViewTests(unittest.TestCase):
    def test_spec_view_is_public_and_the_data_views_are_not(self) -> None:
        self.assertFalse(views.OpenApiView.requires_auth)
        for view in views.VIEWS:
            if view is not views.OpenApiView:
                self.assertTrue(getattr(view, "requires_auth", True), view.__name__)


if __name__ == "__main__":
    unittest.main()
