#pragma once
// The Message page.

#include "palette.h"
#include "state.h"
#include "text.h"

namespace cgotchi {
namespace ui {

constexpr size_t kMessageWidth = 18;   // characters per line

inline void draw_message_page(Display &it, const Palette &p, const Fonts &f, const State &s) {
  it.print(120, 24, f.med, p.accent, TextAlign::TOP_CENTER, s.message_title.c_str());
  it.filled_rectangle(20, 64, 200, 2, p.secondary);
  int y = 80;
  for (const auto &line : wrap_text(s.message_body, kMessageWidth)) {
    it.print(18, y, f.small, p.secondary, TextAlign::TOP_LEFT, line.c_str());
    y += 26;
  }
}

}  // namespace ui
}  // namespace cgotchi
