#pragma once
// The Face page: the face (components/face) and a status line under it.

#include "esphome/components/face/face.h"
#include "palette.h"
#include "state.h"

namespace cgotchi {
namespace ui {

inline void draw_face_page(Display &it, const Palette &p, const Fonts &f, const State &s) {
  auto &face = cgotchi::face::instance();
  face.visible = true;
  const int expression = s.booting() ? 0 : (s.reaction >= 0 ? s.reaction : s.expression);
  face.update({(cgotchi::face::Expression) expression, (cgotchi::face::Voice) s.voice, s.speaking(), s.booting()},
              s.now_ms);
  face.draw(it, p.accent, p.bg, s.now_ms);

  if (s.speaking()) it.print(120, 262, f.small, p.dim, TextAlign::TOP_CENTER, "speaking...");
  else if (s.voice == 1) it.print(120, 262, f.small, p.accent, TextAlign::TOP_CENTER, "listening...");
  else if (s.voice == 2) it.print(120, 262, f.small, p.dim, TextAlign::TOP_CENTER, "thinking...");
  else if (s.voice == 4) it.print(120, 262, f.small, Color(255, 80, 80), TextAlign::TOP_CENTER, "voice error");
  if (s.booting() && s.now_ms >= 1200) it.print(120, 255, f.med, p.accent, TextAlign::TOP_CENTER, "Hello!");
}

}  // namespace ui
}  // namespace cgotchi
