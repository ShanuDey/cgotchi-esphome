#include "lis2dh12.h"

#include "esphome/core/helpers.h"
#include "esphome/core/log.h"

namespace esphome::lis2dh12 {

static const char *const TAG = "lis2dh12";

static constexpr uint8_t REG_WHO_AM_I = 0x0F;
static constexpr uint8_t REG_CTRL1 = 0x20;
static constexpr uint8_t REG_CTRL4 = 0x23;
static constexpr uint8_t REG_OUT_X_L = 0x28;
static constexpr uint8_t AUTO_INCREMENT = 0x80;
static constexpr uint8_t WHO_AM_I_VALUE = 0x33;
static constexpr uint8_t CTRL1_100HZ_XYZ = 0x57;
static constexpr uint8_t CTRL4_BDU_HIGH_RES = 0x88;
static constexpr float G_PER_LSB = 0.001f;   // 12-bit high-res mode at +-2 g

bool Lis2dh12Component::configure_() {
  uint8_t who = 0;
  if (!this->read_byte(REG_WHO_AM_I, &who)) {
    ESP_LOGE(TAG, "Failed to read chip ID");
    return false;
  }
  if (who != WHO_AM_I_VALUE) {
    ESP_LOGE(TAG, "Wrong chip ID 0x%02X, expected 0x%02X", who, WHO_AM_I_VALUE);
    return false;
  }
  if (!this->write_byte(REG_CTRL1, CTRL1_100HZ_XYZ) || !this->write_byte(REG_CTRL4, CTRL4_BDU_HIGH_RES)) {
    ESP_LOGE(TAG, "Failed to configure the chip");
    return false;
  }
  return true;
}

void Lis2dh12Component::setup() {
  MotionComponent::setup();
  if (!this->configure_())
    this->mark_failed();
}

void Lis2dh12Component::dump_config() {
  ESP_LOGCONFIG(TAG, "LIS2DH12 accelerometer:");
  LOG_I2C_DEVICE(this);
  if (this->is_failed()) {
    ESP_LOGE(TAG, "  Communication failed");
    return;
  }
  MotionComponent::dump_config();
}

bool Lis2dh12Component::update_data(motion::MotionData &data) {
  if (this->is_failed())
    return false;

  uint8_t raw[6];
  if (!this->read_bytes(REG_OUT_X_L | AUTO_INCREMENT, raw, sizeof(raw))) {
    ESP_LOGW(TAG, "Failed to read acceleration");
    if (++this->failed_reads_ >= 20) {   // about a second: the chip may have reset
      this->failed_reads_ = 0;
      this->configure_();
    }
    return false;
  }
  this->failed_reads_ = 0;
  for (int axis = 0; axis < 3; axis++) {
    const int16_t value = (int16_t) encode_uint16(raw[2 * axis + 1], raw[2 * axis]) >> 4;   // left-justified
    data.acceleration[axis] = value * G_PER_LSB;
  }
  return true;
}

}  // namespace esphome::lis2dh12
