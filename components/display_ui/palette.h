#pragma once
// The screen colors, worked out from the three theme lights. The text (fg) and hint (dim) colors
// follow the background (light on dark, dark on light). An accent or secondary too close to the
// background is pushed away from it so it never vanishes. Dim themes get dimmer text.

#include <math.h>

#include "themes.h"
#include "esphome/core/color.h"

namespace cgotchi {
namespace ui {

struct Palette {
  esphome::Color bg, fg, dim, accent, secondary;
  bool light_bg;
};

inline float luminance(float r, float g, float b) { return 0.2126f * r + 0.7152f * g + 0.0722f * b; }

inline esphome::Color to_color(float r, float g, float b) {
  return esphome::Color((uint8_t) (r * 255), (uint8_t) (g * 255), (uint8_t) (b * 255));
}

// Moves a color away from the background (luminance `bl`) until it is readable.
inline void fit_to_background(float &r, float &g, float &b, float bl, bool light_bg) {
  const float l = luminance(r, g, b);
  if (light_bg) {
    const float maxl = bl - 0.5f;
    if (l > maxl) {
      const float f = l > 0.0f ? maxl / l : 0.0f;
      r *= f;
      g *= f;
      b *= f;
    }
  } else {
    const float minl = bl + 0.15f;
    if (l <= 0.0f) {
      r = g = b = minl;
    } else if (l < minl) {
      const float f = minl / l;
      r = fminf(r * f, 1.0f);
      g = fminf(g * f, 1.0f);
      b = fminf(b * f, 1.0f);
    }
  }
}

// L is a light::LightState. Accent and secondary ignore on/off; for the background, off is black.
template <typename L>
inline Palette make_palette(L *bg_light, L *accent_light, L *secondary_light) {
  float br, bgn, bb;
  light_color(bg_light, true, br, bgn, bb);
  const float bl = luminance(br, bgn, bb);
  const bool light_bg = bl > 0.5f;

  float ar, ag, ab, sr, sg, sb;
  light_color(accent_light, false, ar, ag, ab);
  light_color(secondary_light, false, sr, sg, sb);
  fit_to_background(ar, ag, ab, bl, light_bg);
  fit_to_background(sr, sg, sb, bl, light_bg);

  // On a dark background, dim the text when the theme colors are dim (night themes).
  uint8_t fg_v = 0, dim_v = 110;
  if (!light_bg) {
    const float k = fminf(1.0f, fmaxf(0.5f, fmaxf(luminance(ar, ag, ab), luminance(sr, sg, sb)) / 0.5f));
    fg_v = (uint8_t) (255 * k);
    dim_v = (uint8_t) (130 * k);
  }

  return {to_color(br, bgn, bb), esphome::Color(fg_v, fg_v, fg_v), esphome::Color(dim_v, dim_v, dim_v),
          to_color(ar, ag, ab),
          to_color(sr, sg, sb),
          light_bg};
}

}  // namespace ui
}  // namespace cgotchi
