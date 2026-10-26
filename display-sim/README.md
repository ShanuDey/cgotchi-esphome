# Display simulator

Runs the real `face` component on your PC, with no device. It opens a 240x296 window
using ESPHome's [host platform and SDL display](https://esphome.io/components/display/sdl/),
so the same C++ that runs on the board draws what you see. Use it to tune faces and check
animation before flashing.

It stands in for Home Assistant: the control page sets the same entities HA sets on the
device (page, expression, voice state, speaking, theme colors, clock and message text, frame rate). The Face, Clock and
Message pages are simulated; Display Frame and WebView (they need the network), audio, touch, Wi-Fi and the real HA
connection are not.

## One-time setup (Windows 11)

The host platform needs Linux, so it runs in WSL. Everything else stays on Windows.

1. WSL with Ubuntu: `wsl --install -d Ubuntu` (skip if `wsl -l -v` already lists it).
2. In Ubuntu, install the compiler and SDL2:

   ```bash
   sudo apt update && sudo apt install -y build-essential libsdl2-dev pkg-config
   ```

3. In Ubuntu, install `uv`:

   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

The simulator keeps its own Linux Python environment and build output in your WSL home
(`~/.venvs/cgotchi`, `~/.esphome-sim`), so the repo's Windows `.venv` and `.esphome` are
not touched. The window appears through WSLg, which ships with Windows 11.

## Run with the control page (recommended)

From the repo root in PowerShell (or any shell on Linux or macOS):

```powershell
uv run display-sim/control.py
```

This starts the simulator in WSL, opens the control page at <http://localhost:8081>, and
stops the simulator when you press Ctrl+C. The first build is slow. Options:
`--no-sim` (only the page, start the simulator yourself), `--no-browser`, `--port`,
`--distro` (the WSL distribution, default Ubuntu).

Put the page and the simulator window side by side (Win+Left and Win+Right): the page fills
the width it is given.

## Tuning a face

Faces are numbers in [components/face/looks.h](../components/face/looks.h). To change one:

1. Edit the numbers (for example `mouth_curve` in `happy()`), and save.
2. Press **Restart simulator** on the page. The rebuild takes about a second, then the window
   reopens. Your settings stay as they were.

The same numbers drive the device, so what you see is what a flash would give you. To see an
expression, pick it on the page; to see it move, change between expressions, or set a voice
state or speaking.

## Run the simulator alone

```powershell
wsl -d Ubuntu -- bash <localrepo_path>/display-sim/run.sh
```

or from an Ubuntu shell, `./display-sim/run.sh`. Arguments: `config` (validate only),
`compile`, or `run` (the default: build and open the window).

## Settings file

The simulator polls `settings.txt` (created from `settings.example.txt` on the first run,
git-ignored) and applies it whenever it changes. The control page writes it, and you can edit
it by hand in any editor: saving applies the change within a fraction of a second. The file is
the whole state, so a line you delete goes back to its default. Bad lines are logged and
skipped. See the comments in [settings.example.txt](settings.example.txt) for every key.

## Keys

Click the window first so it has focus.

| Key | Action |
|---|---|
| Left / Right | previous / next expression |
| V | next voice state (Idle, Listening, Thinking, Replying, Error) |
| S | toggle speaking |
| P | next page (Face, Clock, Message) |
| Up / Down | frame rate +5 / -5 fps |

Keys change the running simulator only, not `settings.txt`, so the next edit of the file or
the page puts everything back to what it says.

## What the page expects from the face headers

`simctl/face_headers.py` reads the expression and voice names from the enums in
`components/face/looks.h`, and the themes from `components/display_ui/themes.h`, with simple patterns. Keep
their existing style. If it drifts, the page stops at startup with a message saying what it
could not find. A new expression or color shows up on the page after a restart.

## Layout

| Path | Role |
|---|---|
| `display-sim.yaml` | the simulator's ESPHome config (SDL window, settings polling, key bindings) |
| `run.sh` | runs it in WSL |
| `control.py`, `simctl/` | the control page's FastAPI server (see the module list in `simctl/__init__.py`) |
| `tests/` | pytest tests for the parsers, the settings file and the API |
| `web/` | the page: plain HTML, CSS and JavaScript, no build step |
| `settings.example.txt` | documented template for `settings.txt` |

## Tests

```powershell
uv run pytest display-sim/tests
```

CI ([check.yml](../.github/workflows/check.yml)) runs these, builds the simulator (which compiles the
shared C++ headers) and validates the device config. To validate the simulator config yourself, run
`./run.sh config` in WSL: ESPHome's SDL display needs
`sdl2-config`, so `esphome config` does not work on Windows.

## Keeping it in step with the device

The device and the simulator draw with the same code: `cgotchi::ui::render()` in
[components/display_ui/ui.h](../components/display_ui/ui.h). Edits to a page, an expression or the colors
show up in both with no copying. Only the entities are mirrored by hand: the option lists in
`display-sim.yaml` (pages, expressions, voices, clock format) must match the device's, and so
must the message text limits (`MESSAGE_TITLE_MAX` and `MESSAGE_BODY_MAX` in `simctl/meta.py`).
