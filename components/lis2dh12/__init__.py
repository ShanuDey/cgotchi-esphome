import esphome.codegen as cg
from esphome.components import i2c
from esphome.components.motion import MotionComponent

DEPENDENCIES = ["i2c", "motion"]

lis2dh12_ns = cg.esphome_ns.namespace("lis2dh12")
Lis2dh12Component = lis2dh12_ns.class_("Lis2dh12Component", MotionComponent, i2c.I2CDevice)

CONFIG_SCHEMA = {}
