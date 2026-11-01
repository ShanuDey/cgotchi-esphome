"""Cgotchi: an HTTP API over the cgotchi ESPHome device."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_DEVICE_ID
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .device import CgotchiDevice
from .views import VIEWS

_REGISTERED_KEY = f"{DOMAIN}_views_registered"


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    hass.data[DOMAIN] = CgotchiDevice(hass, entry.data[CONF_DEVICE_ID])
    # Views cannot be unregistered, so register once; they answer 503 while no device is set up.
    if not hass.data.get(_REGISTERED_KEY):
        for view in VIEWS:
            hass.http.register_view(view())
        hass.data[_REGISTERED_KEY] = True
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    hass.data.pop(DOMAIN, None)
    return True
