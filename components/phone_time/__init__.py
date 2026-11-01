from pathlib import Path

import esphome.codegen as cg
from esphome.components import web_server_base
from esphome.components.web_server_base import CONF_WEB_SERVER_BASE_ID
import esphome.config_validation as cv
from esphome.const import CONF_ID

# Serves /time (time.html, with time.js inlined at build): sends the browser's clock to the "Set Time" text entity,
# then opens the controls.
SCRIPT_TAG = '<script src="time.js"></script>'
AUTO_LOAD = ["web_server_base"]
CODEOWNERS = []

phone_time_ns = cg.esphome_ns.namespace("phone_time")
PhoneTime = phone_time_ns.class_("PhoneTime", cg.Component)

CONFIG_SCHEMA = cv.Schema(
    {
        cv.GenerateID(): cv.declare_id(PhoneTime),
        cv.GenerateID(CONF_WEB_SERVER_BASE_ID): cv.use_id(web_server_base.WebServerBase),
    }
).extend(cv.COMPONENT_SCHEMA)


async def to_code(config):
    base = await cg.get_variable(config[CONF_WEB_SERVER_BASE_ID])
    var = cg.new_Pvariable(config[CONF_ID], base)
    await cg.register_component(var, config)
    here = Path(__file__).parent
    page = (here / "time.html").read_text(encoding="utf-8")
    if SCRIPT_TAG not in page:
        raise cv.Invalid(f"time.html must contain {SCRIPT_TAG}")
    script = (here / "time.js").read_text(encoding="utf-8")
    if "</script" in script.lower():
        raise cv.Invalid("time.js must not contain </script")
    cg.add(var.set_page(page.replace(SCRIPT_TAG, f"<script>\n{script}</script>")))
