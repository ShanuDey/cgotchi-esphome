# Display pages and settings

The display has five pages. Change page with a long press of Volume Down or the
**Display Page** select in HA. The select is not restored on boot, so a reboot
lands on Face.

| Page | Shows |
|---|---|
| Face | Animated face. The color, expression and mouth react to voice and audio. |
| Clock | Time and date from HA. |
| Message | **Message Title** and **Message Body**, set from HA. |
| Display Frame | JPEG snapshots from a URL: [display-frame.md](display-frame.md). |
| WebView | A live web page: [webview.md](webview.md). |

While audio plays, or the voice assistant is running, the face talks whatever page
is selected (the **Display Page** select does not change).

## Face

**Face Expression** (Happy, Sad, Sleepy, Surprised, Angry, Laughing, Confused,
Love, Wink).

## Theme colors

Three color lights theme the Face, Clock and Message pages. The Display Frame and
WebView pages draw their own content and are not themed.

The **Theme** select sets all three lights at once: Classic (default), Midnight,
Bubblegum, Forest, Sunset, Grape, Ocean, Lava, Paper and Mint. Paper and Mint are light
themes. It shows **Custom** when the three lights match no theme (picking Custom does
nothing), so you can start from a theme and then adjust one light. The themes live in
[themes.h](../components/display_ui/themes.h); keep their names in sync with the select options
in `cgotchi.yaml`, in the same order.

Each light also has a color picker, and its brightness slider scales the color. The
on/off switch does nothing, except for the background, where off is black.

| Entity | Used for |
|---|---|
| **Accent Color** | The headline color: the face, clock digits, message title, volume and update bars. Default blue. |
| **Secondary Color** | Supporting text: message body, clock date, dividers and the volume border. Default light cyan. |
| **Background Color** | The page background, dark or light. Off is black, and that is the default. The text and hint colors switch between white and black to match, and an accent or secondary too close to the background is pushed lighter or darker so it stays readable. |

Status colors stay fixed on every page: the green mic dot, red errors and gray hints.
A very dark accent or secondary is brightened so it stays visible on the background.

The face is drawn by the header-only `face` component, split by concern:

| File | Role |
|---|---|
| [looks.h](../components/face/looks.h) | The `Shape` model (eye size, lids, gaze, mouth) and one function per expression. |
| [draw.h](../components/face/draw.h) | Draws one frame from a `Shape`. No state, no timing. |
| [face.h](../components/face/face.h) | Eases between expressions, blinks, glances around, reacts to voice and audio. |

The screen around the face is drawn by the header-only `display_ui` component. The device and
the display simulator both call its `render()`, so they draw the same thing. ESPHome copies only
the files directly in a component's folder, so the pages are flat files named `<page>_page.h`:

| File | Role |
|---|---|
| [ui.h](../components/display_ui/ui.h) | `render()`: picks the page and draws the popups over it. |
| [state.h](../components/display_ui/state.h) | `State`: everything a frame depends on, as plain values the YAML fills in. |
| [face_page.h](../components/display_ui/face_page.h) | The Face page: the face and its status line. |
| [clock_page.h](../components/display_ui/clock_page.h) | The Clock page. |
| [message_page.h](../components/display_ui/message_page.h) | The Message page, with word wrap. |
| [frame_page.h](../components/display_ui/frame_page.h) | The Display Frame page. |
| [widgets.h](../components/display_ui/widgets.h) | The volume popup, the mic dot and the firmware update screen. |
| [themes.h](../components/display_ui/themes.h) | The ten themes, and reading and setting the three theme lights. |
| [palette.h](../components/display_ui/palette.h) | Works out the screen colors (background, text, hint, accent, secondary) from the three theme lights. |
| [text.h](../components/display_ui/text.h) | Word wrap, URL encoding and line splitting. Plain C++, tested in [tests/](../components/display_ui/tests/test_text.cpp). |

Between expressions the face morphs rather than snapping. While nothing moves, it
redraws only for the occasional blink or glance, which keeps battery use low.
**Face Frame Rate** (5 to 25 fps) caps how often it may redraw while animating:
lower saves battery and leaves more time for audio, higher is smoother.

To tune an expression without flashing, use the [display simulator](../display-sim/README.md):
it runs this same component on your PC with a control page and a slider for every shape field.

To add an expression: write a function in `looks.h`, add it to the `Expression`
enum and to `looks()`, and add its name to the **Face Expression** select in
`cgotchi.yaml` in the same order. 

## Clock

**Clock Format** selects 12 or 24 hour (no AM/PM). There is no battery-backed
clock: after power-off the Clock page shows "waiting for time" until the board
reconnects to HA and syncs.

## Boot and updates

- **Boot animation:** eyes open and "Hello!" appears for the first ~2.6 s after power on.
- **OTA progress:** "Updating" with a percentage, or "Update failed". It only
  appears if the firmware already running has it, so it shows from the second flash
  after adding it.

## Rounded corners

The panel is a 240x296 rectangle, but the bezel and glass have rounded corners
that hide the pixels in all four corners (the radius is not measured; about
25 to 30 px is a guess). Keep text, icons and anything important about 16 to
20 px away from the corners, in display lambdas, display frames and website
screenshots alike. The Face, Clock and Message pages are centred and already
fit. Content in the middle of each edge stays visible.

## Saved settings

**Clock Format**, **Face Expression**, **Theme**, the three theme color lights, **Message Title/Body**
and **Display Frame URL** use `restore_value: true`, so they live in flash and
survive power-off, reboots and OTA. Renaming one or changing its options in
the YAML resets it to the default once; a full flash erase clears them all.

## Display notes

- `transform:` needs all three keys (`swap_xy`, `mirror_x`, `mirror_y`).
- The display redraws on any display-entity change, once a minute, and while audio
  plays (`update_interval: never`).
