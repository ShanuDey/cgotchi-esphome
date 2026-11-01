#pragma once
// Drawn over, or instead of, a page: volume popup, mic dot, firmware update screen.

#include "palette.h"
#include "state.h"

namespace cgotchi {
namespace ui {

// Kept inside the bottom safe margin: the screen corners are cropped.
inline void draw_volume(Display &it, const Palette &p, const Fonts &f, const State &s) {
  it.filled_rectangle(12, 244, 216, 38, p.bg);
  it.rectangle(12, 244, 216, 38, p.secondary);
  it.rectangle(24, 255, 130, 16, p.fg);
  it.filled_rectangle(26, 257, (126 * s.volume_pct) / 100, 12, p.accent);
  it.printf(192, 263, f.small, p.fg, TextAlign::CENTER, "%d%%", s.volume_pct);
}

// Green dot while the mic is open.
inline void draw_mic(Display &it, const State &s) {
  if (s.mic_on) it.filled_circle(120, 12, 6, Color(0, 220, 90));
}

// Replaces everything else.
inline void draw_ota(Display &it, const Palette &p, const Fonts &f, const State &s) {
  if (s.ota_state == OTA_FAILED) {
    it.print(120, 120, f.med, Color(255, 80, 80), TextAlign::TOP_CENTER, "Update failed");
    return;
  }
  it.print(120, 80, f.med, p.accent, TextAlign::TOP_CENTER, "Updating");
  it.rectangle(20, 140, 200, 18, p.dim);
  it.filled_rectangle(22, 142, (196 * s.ota_pct) / 100, 14, p.accent);
  it.printf(120, 175, f.med, p.fg, TextAlign::TOP_CENTER, "%d%%", s.ota_pct);
  it.print(120, 250, f.small, p.dim, TextAlign::TOP_CENTER, "Don't unplug");
}

}  // namespace ui
}  // namespace cgotchi
