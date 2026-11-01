#pragma once
// Face renderer: turns one Frame into drawing calls. Pure drawing, no state and no timing, so it
// also runs on a PC (tools/face_preview). `It` is the ESPHome display (or a test canvas) and
// `Color` its color type.

#include <math.h>
#include <stdint.h>

#include "looks.h"

namespace cgotchi {
namespace face {

constexpr int kCenterX = 120;   // the panel is 240 px wide

// Everything needed to draw one frame: the animated shape plus the effects drawn over it.
struct Frame {
  Shape shape;
  float blink = 0;       // 0 open .. 1 shut
  bool hearts = false;   // hearts instead of eyes
  bool spiral = false;   // spirals instead of eyes
  Overlay overlay = Overlay::None;
  uint32_t now = 0;      // animates the spiral and the overlays
  float heart_size = 56;
  int ring = -1;         // >= 0: attention rings around the eyes, this many px wider than the eye
  int dots = -1;         // >= 0: three "thinking" dots instead of a mouth, this one lit
};

namespace detail {

template <typename It, typename Color>
void round_rect(It &it, int x, int y, int w, int h, int r, Color c) {
  if (w < 1 || h < 1) return;
  if (r > w / 2) r = w / 2;
  if (r > h / 2) r = h / 2;
  it.filled_rectangle(x + r, y, w - 2 * r, h, c);
  it.filled_rectangle(x, y + r, w, h - 2 * r, c);
  it.filled_circle(x + r, y + r, r, c);
  it.filled_circle(x + w - 1 - r, y + r, r, c);
  it.filled_circle(x + r, y + h - 1 - r, r, c);
  it.filled_circle(x + w - 1 - r, y + h - 1 - r, r, c);
}

// side: -1 left eye, +1 right eye. open: 1 fully open .. 0 shut, shrinks the eye and its lids
// together (blink, wink). The lids are drawn in the background color over the eye.
template <typename It, typename Color>
void eye(It &it, int cx, int cy, const Shape &s, float open, float tilt, int side, Color fg, Color bg) {
  const int w = (int) s.eye_w, hh = (int) fmaxf(4.0f, s.eye_h * open);
  const int x0 = cx - w / 2, y0 = cy - hh / 2, x1 = x0 + w - 1, y1 = y0 + hh - 1;
  const float lid_top = s.lid_top * open, lid_bot = s.lid_bot * open;
  tilt *= open;
  round_rect(it, x0, y0, w, hh, (int) s.eye_r, fg);

  if (lid_top >= 1) it.filled_rectangle(x0 - 1, y0 - 1, w + 2, (int) lid_top + 1, bg);
  if (fabsf(tilt) >= 1) {
    // The lid is a triangle across the top whose third corner dips by |tilt|. Angry dips the
    // corner next to the nose, sad the corner away from it.
    const int inner = side < 0 ? x1 : x0, outer = side < 0 ? x0 : x1;
    const int dip_x = tilt > 0 ? inner : outer;   // which top corner the lid dips towards
    it.filled_triangle(x0 - 1, y0 - 1, x1 + 1, y0 - 1, dip_x, y0 + (int) fabsf(tilt), bg);
  }
  if (lid_bot >= 1) {
    // A large background circle rising from below: a curved lower lid (cheek).
    const int r = (int) (s.eye_w * 0.8f);
    it.filled_circle(cx, y1 + r - (int) lid_bot, r, bg);
  }
}

template <typename It, typename Color>
void heart(It &it, int cx, int cy, float size, Color c) {
  const int r = (int) (size * 0.27f), dx = (int) (size * 0.24f), top = cy - (int) (size * 0.12f);
  it.filled_circle(cx - dx, top, r, c);
  it.filled_circle(cx + dx, top, r, c);
  it.filled_triangle(cx - (int) (size * 0.5f), top + 3, cx + (int) (size * 0.5f), top + 3, cx, cy + (int) (size * 0.48f), c);
}

// Bent mouth line drawn with a round brush, so it is as thick on a steep bend as on a flat part
// and ends in round caps. amp > 0 bends the middle down (smile), amp < 0 up (frown).
template <typename It, typename Color>
void mouth_line(It &it, int cx, int y, int w, float amp, Color c) {
  constexpr int kBrush = 4;      // brush radius: the line is 2 * kBrush + 1 px thick
  constexpr int kSegments = 32;
  for (int i = 0; i <= kSegments; i++) {
    const float t = i / (float) kSegments;
    const int x = cx - w / 2 + (int) (w * t);
    const int yy = y + (int) (amp * sinf(t * 3.14159265f));
    it.filled_circle(x, yy, kBrush, c);
  }
}

// Spiral winding outwards from the center; dir flips the spin.
template <typename It, typename Color>
void spiral(It &it, int cx, int cy, float phase, float dir, Color c) {
  constexpr int kPoints = 90;
  constexpr float kTurns = 2.5f, kRadius = 27.0f;
  for (int i = 0; i <= kPoints; i++) {
    const float t = i / (float) kPoints;
    const float a = dir * (phase + t * kTurns * 6.2831853f);
    it.filled_circle(cx + (int) (kRadius * t * cosf(a)), cy + (int) (kRadius * t * sinf(a)), 3, c);
  }
}

// A "Z" about s px wide, three pixels thick.
template <typename It, typename Color>
void zee(It &it, int x, int y, int s, Color c) {
  for (int k = -1; k <= 1; k++) {
    it.line(x, y + k, x + s, y + k, c);
    it.line(x + s + k, y, x + k, y + s, c);
    it.line(x, y + s + k, x + s, y + s + k, c);
  }
}

// Three Zs rising up and to the right, growing as they go.
template <typename It, typename Color>
void zzz(It &it, uint32_t now, Color c) {
  for (int k = 0; k < 3; k++) {
    const float p = fmodf(now / 2800.0f + k / 3.0f, 1.0f);
    zee(it, 140 + (int) (45 * p), 92 - (int) (44 * p), 8 + (int) (14 * p), c);
  }
}

template <typename It, typename Color>
void confetti(It &it, uint32_t now) {
  static const uint8_t kColors[][3] = {{255, 90, 90}, {255, 200, 60}, {90, 220, 120}, {80, 170, 255}, {230, 110, 255}};
  for (uint32_t i = 0; i < 16; i++) {
    const uint32_t h = (i + 1) * 2654435761u;
    const int x = 24 + (int) ((h >> 8) % 192);
    const float speed = 50.0f + (float) ((h >> 4) % 60);
    const float t = fmodf(now / 1000.0f, 296.0f / speed);   // one period keeps the float exact after days
    const int y = (int) fmodf((float) ((h >> 16) % 296) + t * speed, 296.0f);
    const uint8_t *k = kColors[i % 5];
    it.filled_rectangle(x, y, 6, 6, Color(k[0], k[1], k[2]));
  }
}

template <typename It, typename Color>
void sweat(It &it) {
  const Color c(120, 200, 255);
  it.filled_circle(206, 98, 7, c);
  it.filled_triangle(206, 78, 199, 94, 213, 94, c);
}

}  // namespace detail

template <typename It, typename Color>
void draw(It &it, const Frame &f, Color fg, Color bg) {
  const Shape &s = f.shape;
  const int ey = (int) (s.eye_y + s.look_y);
  const int lx = kCenterX - (int) (s.eye_gap / 2) + (int) s.look_x;
  const int rx = kCenterX + (int) (s.eye_gap / 2) + (int) s.look_x;

  if (f.hearts) {
    detail::heart(it, lx, ey, f.heart_size, fg);
    detail::heart(it, rx, ey, f.heart_size, fg);
  } else if (f.spiral) {
    const float phase = f.now / 180.0f;
    detail::spiral(it, lx, ey, phase, 1.0f, fg);
    detail::spiral(it, rx, ey, phase, -1.0f, fg);
  } else {
    const float open = 1 - f.blink;
    const float right_open = open * fmaxf(0.0f, 1 - s.wink / s.eye_h);
    detail::eye(it, lx, ey, s, open, s.lid_tilt - s.lid_asym, -1, fg, bg);
    detail::eye(it, rx, ey, s, right_open, s.lid_tilt + s.lid_asym, +1, fg, bg);
    if (f.ring >= 0) {
      const int r = (int) (s.eye_h / 2) + f.ring + 6;
      it.circle(lx, ey, r, fg);
      it.circle(rx, ey, r, fg);
    }
  }

  const int my = (int) s.mouth_y;
  if (f.dots >= 0) {
    for (int d = 0; d < 3; d++) it.filled_circle(kCenterX - 28 + d * 28, my, d == f.dots ? 9 : 5, fg);
  } else if (s.mouth_w >= 2) {
    if (s.mouth_open >= 2) {
      const int w = (int) s.mouth_w, h = (int) s.mouth_open;
      detail::round_rect(it, kCenterX - w / 2, my - h / 2, w, h, h / 2, fg);
    } else {
      detail::mouth_line(it, kCenterX, my, (int) s.mouth_w, s.mouth_curve, fg);
    }
  }

  switch (f.overlay) {
    case Overlay::Zzz: detail::zzz(it, f.now, fg); break;
    case Overlay::Confetti: detail::confetti<It, Color>(it, f.now); break;
    case Overlay::Sweat: detail::sweat<It, Color>(it); break;
    default: break;
  }
}

}  // namespace face
}  // namespace cgotchi
