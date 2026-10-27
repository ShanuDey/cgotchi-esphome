from esphome.components import i2c
from esphome.components.motion import motion_schema, new_motion_component
from esphome.types import ConfigType

from . import Lis2dh12Component

CONFIG_SCHEMA = motion_schema(Lis2dh12Component, has_accel=True, has_gyro=False).extend(i2c.i2c_device_schema(0x19))


async def to_code(config: ConfigType) -> None:
    var = await new_motion_component(config)
    await i2c.register_i2c_device(var, config)
