#pragma once
// The Display Frame page: the latest snapshot, or a status while there is none.

#include "palette.h"
#include "state.h"

namespace cgotchi {
namespace ui {

inline void draw_frame_page(Display &it, const Palette &p, const Fonts &f, const State &s) {
  if (s.frame_state == FRAME_PLAYING) {
    if (s.frame_image != nullptr) it.image(0, 0, s.frame_image);
  } else if (s.frame_state == FRAME_LOADING) {
    it.print(120, 140, f.med, p.dim, TextAlign::CENTER, "Loading...");
  } else {
    it.print(120, 130, f.med, p.fg, TextAlign::CENTER, "No frame");
    it.print(120, 170, f.small, p.dim, TextAlign::CENTER, "check Frame URL");
  }
}

}  // namespace ui
}  // namespace cgotchi
