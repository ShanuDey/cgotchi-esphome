#pragma once
// ST LIS2DH12 accelerometer as an ESPHome motion device: 12-bit, +-2 g, 100 Hz.

#include "esphome/components/i2c/i2c.h"
#include "esphome/components/motion/motion_component.h"

namespace esphome::lis2dh12 {

class Lis2dh12Component : public motion::MotionComponent, public i2c::I2CDevice {
 public:
  void setup() override;
  void dump_config() override;

 protected:
  bool update_data(motion::MotionData &data) override;
  bool configure_();

  uint8_t failed_reads_{0};
};

}  // namespace esphome::lis2dh12
