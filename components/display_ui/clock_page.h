#pragma once
// The Clock page.

#include <stdio.h>

#include "palette.h"
#include "state.h"

namespace cgotchi {
namespace ui {

inline void draw_clock_page(Display &it, const Palette &p, const Fonts &f, const State &s) {
  if (!s.time.is_valid()) {
    it.print(120, 130, f.med, p.dim, TextAlign::TOP_CENTER, "waiting for time");
    return;
  }
  char hm[8];
  if (s.hour24) {
    snprintf(hm, sizeof(hm), "%02d:%02d", s.time.hour, s.time.minute);
  } else {   // no AM/PM
    int hour12 = s.time.hour % 12;
    if (hour12 == 0) hour12 = 12;
    snprintf(hm, sizeof(hm), "%d:%02d", hour12, s.time.minute);
  }
  it.print(120, 90, f.clock, p.accent, TextAlign::TOP_CENTER, hm);
  it.strftime(120, 180, f.med, p.secondary, TextAlign::TOP_CENTER, "%a %d %b", s.time);
}

}  // namespace ui
}  // namespace cgotchi
