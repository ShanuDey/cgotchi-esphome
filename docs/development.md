# Development

## How the components are sourced

`cgotchi.yaml` loads its three custom components from GitHub:

```yaml
external_components:
  - source:
      type: git
      url: https://github.com/ShanuDey/cgotchi-esphome
      ref: ${components_ref}
      path: components
    components: [remote_webview, display_ui, face]
```

- `remote_webview`: the WebView client, a patched copy of strange-v's
  RemoteWebViewClient.
- `face`: header-only; the face expressions, animation and drawing.
- `display_ui`: header-only; draws the screen (one header per page), the themes and colors.
  Loads `face` with it. See [display-pages.md](display-pages.md#face).

This is what lets the config work standalone in the HA builder with no local
files. The catch: edits to `components/` have no effect on a build until you push
them. To iterate on a component locally, run ESPHome through `dev.py` (from
the repo root) instead of `uv run esphome`:

```bash
uv run dev.py compile
uv run dev.py run --device <ip|COMx> --no-logs
uv run dev.py logs --device <ip>
```

It writes `cgotchi-dev.yaml` (git-ignored), a copy of `cgotchi.yaml` with only the
component source switched to `components/` in this checkout. `cgotchi.yaml` is never
edited, so there is nothing to change back. Use plain `uv run esphome ... cgotchi.yaml`
to build what the branch on GitHub will give users.

ESPHome caches the git clone; use `esphome config --clean` (or delete the cached
clone under `.esphome/`) after pushing a change.

## Config layout

`cgotchi.yaml` holds the device identity and core services and lists the feature files in
`packages/`: `hardware.yaml`, `display.yaml`, `voice.yaml`, `controls.yaml` and
`webview.yaml`. Each file starts with what it uses from the others. C++ for the display lives in
`components/display_ui/` (`ui.h` draws the pages), not in the YAML, so lambdas stay short and the
display simulator draws the same thing. `esphome config cgotchi.yaml` prints the merged result.

## Pin a tag or test a branch

In the HA builder the config and the components are fetched separately, so name the tag or
branch twice. Push it first: the builder reads GitHub, not your PC.

```yaml
substitutions:
  components_ref: my-branch   # or a tag such as v0.1.0

packages:
  cgotchi:
    url: https://github.com/ShanuDey/cgotchi-esphome
    ref: my-branch
    files: [cgotchi.yaml]
    refresh: 1min
```

`refresh` stops ESPHome reusing a cached clone for a day.

## Releasing

1. Merge to `main` and tag a release (for example `v0.1.0`).
2. Point `components_ref` in `cgotchi.yaml` and the `packages:` line in
   [install.md](install.md) at the tag, so users don't break when the branch moves.

## Other folders

- [display-frame/](../display-frame/README.md): the display-frame service.
- [remote-webview/](../remote-webview/): Docker Compose for the Remote WebView server.
- `wyoming-voice/`: Docker Compose for local Wyoming speech services (Piper and Whisper) for the Assist pipeline.
