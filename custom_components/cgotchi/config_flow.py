"""Config flow: pick the ESPHome device that is the cgotchi."""

from __future__ import annotations

import voluptuous as vol
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_DEVICE_ID
from homeassistant.helpers.selector import DeviceSelector, DeviceSelectorConfig

from .const import DOMAIN


class CgotchiConfigFlow(ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input: dict | None = None) -> ConfigFlowResult:
        if user_input is not None:
            return self.async_create_entry(title="Cgotchi", data=user_input)
        schema = vol.Schema(
            {
                vol.Required(CONF_DEVICE_ID): DeviceSelector(
                    DeviceSelectorConfig(integration="esphome")
                )
            }
        )
        return self.async_show_form(step_id="user", data_schema=schema)
