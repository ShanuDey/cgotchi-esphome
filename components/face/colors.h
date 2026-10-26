#pragma once
// Named colors: the accent presets (display simulator) and the themes of the "Theme" select in
// cgotchi.yaml. Keep the theme names in sync with the select options, in the same order.
#include <cmath>

namespace cgotchi {
namespace face {

struct ColorPreset {
  const char *name;
  float r, g, b;
};

static const ColorPreset FACE_PRESETS[] = {
    {"Blue", 0.0f, 0.78f, 1.0f},   {"Green", 0.2f, 1.0f, 0.3f},  {"Pink", 1.0f, 0.4f, 0.7f},
    {"Orange", 1.0f, 0.55f, 0.0f}, {"Purple", 0.65f, 0.3f, 1.0f}, {"Red", 1.0f, 0.2f, 0.2f},
    {"Yellow", 1.0f, 0.9f, 0.1f},  {"White", 1.0f, 1.0f, 1.0f},
};

// A theme sets the three theme lights together. Values are the final screen colors (0 to 1).
struct Theme {
  const char *name;
  float bg[3], accent[3], secondary[3];
};

static const Theme THEMES[] = {
    {"Classic", {0.0f, 0.0f, 0.0f}, {0.0f, 0.78f, 1.0f}, {0.5f, 0.9f, 1.0f}},
    {"Midnight", {0.02f, 0.02f, 0.07f}, {0.0f, 0.9f, 1.0f}, {0.65f, 0.8f, 1.0f}},
    {"Bubblegum", {0.16f, 0.04f, 0.12f}, {1.0f, 0.4f, 0.7f}, {1.0f, 0.78f, 0.88f}},
    {"Forest", {0.02f, 0.1f, 0.04f}, {0.55f, 1.0f, 0.25f}, {0.75f, 0.95f, 0.8f}},
    {"Sunset", {0.04f, 0.05f, 0.14f}, {1.0f, 0.55f, 0.0f}, {1.0f, 0.85f, 0.4f}},
    {"Grape", {0.09f, 0.03f, 0.16f}, {0.7f, 0.4f, 1.0f}, {0.85f, 0.75f, 1.0f}},
    {"Ocean", {0.0f, 0.09f, 0.11f}, {0.0f, 0.9f, 0.85f}, {0.7f, 0.95f, 0.95f}},
    {"Lava", {0.05f, 0.01f, 0.01f}, {1.0f, 0.2f, 0.15f}, {1.0f, 0.6f, 0.2f}},
    {"Paper", {0.96f, 0.95f, 0.9f}, {0.1f, 0.25f, 0.65f}, {0.35f, 0.4f, 0.5f}},
    {"Mint", {0.88f, 0.97f, 0.92f}, {0.0f, 0.5f, 0.45f}, {0.3f, 0.45f, 0.4f}},
};
static const int THEME_COUNT = sizeof(THEMES) / sizeof(THEMES[0]);

// The three theme lights are plain RGB lights (L is a light::LightState). ESPHome keeps a light's
// RGB at full strength, so the darkness of a color lives in its brightness: the final color is the
// RGB times the brightness. For the background, off is black.
template <typename L>
inline void light_color(L *l, bool off_is_black, float &r, float &g, float &b) {
  const auto &v = l->remote_values;
  const float k = (off_is_black && !v.is_on()) ? 0.0f : v.get_brightness() * v.get_color_brightness();
  r = v.get_red() * k;
  g = v.get_green() * k;
  b = v.get_blue() * k;
}

template <typename L>
inline void set_light_color(L *l, const float c[3]) {
  const float m = fmaxf(c[0], fmaxf(c[1], c[2]));
  if (m <= 0.0f) {
    auto call = l->turn_off();
    call.set_transition_length(0);
    call.perform();
    return;
  }
  auto call = l->turn_on();
  call.set_rgb(c[0] / m, c[1] / m, c[2] / m);
  call.set_brightness(m);
  call.set_color_brightness(1.0f);
  call.set_transition_length(0);
  call.perform();
}

template <typename L>
inline bool light_is(L *l, const float c[3], bool off_is_black) {
  float r, g, b;
  light_color(l, off_is_black, r, g, b);
  return fabsf(r - c[0]) < 0.02f && fabsf(g - c[1]) < 0.02f && fabsf(b - c[2]) < 0.02f;
}

template <typename L>
inline bool theme_is(const Theme &t, L *bg, L *accent, L *secondary) {
  return light_is(bg, t.bg, true) && light_is(accent, t.accent, false) && light_is(secondary, t.secondary, false);
}

}  // namespace face
}  // namespace cgotchi
