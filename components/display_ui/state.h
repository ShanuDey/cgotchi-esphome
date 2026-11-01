#pragma once
// What one frame depends on, as plain values. Headers cannot read entities (no id(...)), so the
// display lambda fills a State and passes it to render() (ui.h).

#include <stdint.h>

#include <string>

#include "esphome/components/display/display.h"
#include "esphome/core/color.h"
#include "esphome/core/time.h"

namespace cgotchi {
namespace ui {

using Display = esphome::display::Display;
using esphome::Color;
using esphome::display::TextAlign;

enum Page { FACE = 0, CLOCK = 1, MESSAGE = 2, DISPLAY_FRAME = 3, WEBVIEW = 4 };   // order of the Display Page select
enum OtaState { OTA_IDLE = 0, OTA_UPDATING = 1, OTA_FAILED = 2 };
enum FrameState { FRAME_LOADING = 0, FRAME_PLAYING = 1, FRAME_MISSING = 2 };

constexpr uint32_t kBootMs = 2600;   // the wake-up animation after power on

struct Fonts {
  esphome::display::BaseFont *clock, *med, *small;
};

struct State {
  uint32_t now_ms = 0;
  int page = FACE;
  int expression = 0;   // index into face::Expression
  int reaction = -1;    // temporary face::Expression over the selected one, -1 for none
  int voice = 0;        // 0 idle, 1 listening, 2 thinking, 3 replying, 4 error
  bool playing = false;   // a reply or media
  bool mic_on = false;    // wake word or assistant
  bool volume_visible = false;
  int volume_pct = 0;
  int ota_state = OTA_IDLE;
  int ota_pct = 0;
  int frame_state = FRAME_LOADING;
  esphome::display::BaseImage *frame_image = nullptr;
  bool hour24 = false;
  esphome::ESPTime time{};
  std::string message_title, message_body;

  bool booting() const { return now_ms < kBootMs; }
  bool speaking() const { return !booting() && playing; }
};

// WebView owns the panel, except while the voice assistant, audio or an update need it.
inline bool shows_webview(const State &s) {
  return s.page == WEBVIEW && s.voice == 0 && !s.booting() && !s.speaking() && s.ota_state == OTA_IDLE;
}

}  // namespace ui
}  // namespace cgotchi
