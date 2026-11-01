import esphome.codegen as cg
import esphome.config_validation as cv

# Header-only component: draws the screen (ui.h), picks the colors and has the text helpers, all
# available to the YAML lambdas. Loads the face component with it.
AUTO_LOAD = ["face"]
CODEOWNERS = []
CONFIG_SCHEMA = cv.Schema({})


async def to_code(config):
    for header in ("ui.h", "themes.h", "text.h"):
        cg.add_global(cg.RawStatement(f'#include "esphome/components/display_ui/{header}"'))
