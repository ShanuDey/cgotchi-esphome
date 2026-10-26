#pragma once
// Draws one frame: picks the page (one *_page.h each) and the popups over it. The device and the
// display simulator both call render(), so they draw the same thing. The WebView page belongs to
// remote_webview, so there render() only draws the volume popup; shows_webview() tells the display
// lambda when to hand the panel over.

#include "clock_page.h"
#include "esphome/components/face/face.h"
#include "face_page.h"
#include "frame_page.h"
#include "message_page.h"
#include "palette.h"
#include "state.h"
#include "widgets.h"

namespace cgotchi {
namespace ui {

inline void render(Display &it, const Palette &p, const Fonts &f, const State &s) {
  cgotchi::face::instance().visible = false;   // the face page sets it

  if (shows_webview(s)) {
    // The tiles pause while the popup shows.
    if (s.volume_visible) draw_volume(it, p, f, s);
    return;
  }

  it.fill(p.bg);

  if (s.ota_state != OTA_IDLE) {
    draw_ota(it, p, f, s);
    return;
  }

  // Audio can play over the frame; the voice assistant takes the screen.
  if (s.page == DISPLAY_FRAME && s.voice == 0 && !s.booting()) {
    draw_frame_page(it, p, f, s);
    draw_mic(it, s);
    if (s.volume_visible) draw_volume(it, p, f, s);
    return;
  }

  int page = s.page;
  if (s.speaking() || s.booting() || s.voice != 0) page = FACE;   // the face talks

  if (page == FACE) draw_face_page(it, p, f, s);
  else if (page == CLOCK) draw_clock_page(it, p, f, s);
  else draw_message_page(it, p, f, s);

  draw_mic(it, s);
  if (s.volume_visible) draw_volume(it, p, f, s);
}

}  // namespace ui
}  // namespace cgotchi
