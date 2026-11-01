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
        "aiohttp": dict(web=types.SimpleNamespace(Request=object, Response=object)),
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


class FakeRequest(dict):
    def __init__(self, user, device, body=None):
        super().__init__(hass_user=user)
        self.app = {"hass": types.SimpleNamespace(data={"cgotchi": device} if device else {})}
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


class SpecViewTests(unittest.TestCase):
    def test_spec_view_is_public_and_the_data_views_are_not(self) -> None:
        self.assertFalse(views.OpenApiView.requires_auth)
        for view in views.VIEWS:
            if view is not views.OpenApiView:
                self.assertTrue(getattr(view, "requires_auth", True), view.__name__)


if __name__ == "__main__":
    unittest.main()
