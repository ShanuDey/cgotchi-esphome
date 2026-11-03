# HTTP API through Home Assistant

The `custom_components/cgotchi` integration adds `/api/cgotchi/...` to Home Assistant. It is a thin layer over
the device's entities (see [ha-entities.md](ha-entities.md)), so it needs no firmware change.

| Endpoint | Does |
|---|---|
| `GET /api/cgotchi/state` | Display, speaker, voice and touch in one call. |
| `GET/POST /api/cgotchi/display` | Page, theme, expression, message, colors, frame rate. |
| `GET/POST /api/cgotchi/speaker` | Play a URL, speak text (needs a `tts.*` entity), volume, play/pause/stop. |
| `GET/POST /api/cgotchi/voice` | On-device wake word on or off. |
| `GET /api/cgotchi/touch` | Last touch gesture, buttons, shake and motion. |
| `POST /api/cgotchi/mcp` | The same operations as MCP tools, for AI agents ([below](#mcp-server)). |

The integration ships its own icon in `custom_components/cgotchi/brand/` (Home Assistant 2026.3 and later).

The microphone is not exposed: the ESPHome API only streams it to the Assist pipeline, which Home Assistant owns.

## Install

Pick one way to get `custom_components/cgotchi/` into Home Assistant:

**HACS** (needs a GitHub release; HACS installs the latest release, or the default branch if there is none):
1. HACS, three-dot menu, Custom repositories. Add `https://github.com/ShanuDey/cgotchi-esphome`, type Integration.
2. Open Cgotchi in HACS, Download, then restart Home Assistant.
3. To try a pre-release, turn on "Show beta versions" in the repository's menu and pick that version.

**From this checkout** (for testing local changes, no push needed): put the Home Assistant config folder (a Samba
share, mount or local path) in `.env` as `CGOTCHI_DEPLOY_DIR`, then run `uv run cgotchi deploy api`. See
[Call it](#call-it) below.

**By hand:** copy `custom_components/cgotchi/` to `<HA config>/custom_components/cgotchi/`.

Then, whichever way you used:
1. Restart Home Assistant (a full restart, not a reload).
2. Settings, Devices & services, Add integration, Cgotchi, pick the ESPHome device.
3. The API is live at `/api/cgotchi/...`. The spec is at `/api/cgotchi/openapi.json` (no token needed).

## Call it

Create a long-lived token for an administrator user (HA profile, Security) and put it in the repo-root `.env` (git-ignored):

```powershell
copy .env.example .env     # then fill in CGOTCHI_HA_TOKEN
uv run cgotchi api state
uv run cgotchi api display --page Message --message-title Hi --message-body "From the API"
uv run cgotchi api display --theme Night --accent-color 0,200,255
uv run cgotchi api speaker --volume 0.5
uv run cgotchi api wake-word on
uv run python -m unittest cgotchi_api.tests.test_api     # script tests
```

To copy the integration into HA while testing, set `CGOTCHI_DEPLOY_DIR` in `.env` (the HA config folder, for
example a Samba share) and run `uv run cgotchi deploy api` (add `--restart` to restart HA afterwards).

`CGOTCHI_HA_URL` is your Home Assistant address on the local network (`http://homeassistant.local:8123`, or the
IP if mDNS fails). Keep any public address in your own `.env`, not in the repo.

## MCP server

`POST /api/cgotchi/mcp` speaks the Model Context Protocol (streamable HTTP, JSON replies, stateless) so an AI agent can
use the device. It needs the same administrator token as the rest of the API and runs inside Home Assistant: nothing
else to deploy. It has one tool per operation in `openapi.yaml`, named by its `operationId`, with the input schema
taken from the spec:

| Tool | Does |
|---|---|
| `get_state` | Display, speaker, voice and touch in one call |
| `get_display`, `set_display` | Read or change page, theme, expression, message, colors, frame rate |
| `get_speaker`, `set_speaker` | Read, or play a URL, speak text, set the volume |
| `get_wake_word`, `set_wake_word` | Read or switch the on-device wake word |
| `get_touch` | Last touch gesture, buttons, shake and motion |

A bad argument or a missing entity comes back as a tool error with a message, not as an HTTP error. There is no
server-to-client stream, so GET answers 405.

Connect Claude Code (use your own Home Assistant address and token):

```
claude mcp add --transport http cgotchi <HA address>/api/cgotchi/mcp --header "Authorization: Bearer <token>"
```

To try the tools in a browser, run `uv run cgotchi mcp ui` (needs Node): it opens the MCP Inspector and prints the
endpoint to enter; choose Streamable HTTP and add the `Authorization: Bearer <token>` header.

Any client that can send a bearer header works the same way (MCP Inspector, any agent framework). A client that only supports
OAuth sign-in may not connect, because Home Assistant's login is not the OAuth discovery MCP clients expect.

To change a tool, edit the operation in `openapi.yaml`; a new operation also needs an entry in `HANDLERS` in
`custom_components/cgotchi/mcp.py`. The tests fail if the two disagree.

## Postman

Import the single file `custom_components/cgotchi/openapi.yaml` into Postman (Import, Files; not the folder) as a
collection, or import the URL `<your HA address>/api/cgotchi/openapi.json` once the integration is running. Then in the collection's Variables tab add `baseUrl` (your HA address) and `token` (a long-lived
access token), and in its Authorization tab choose Bearer Token with `{{token}}`. Check that the request URLs
start with `{{baseUrl}}`. Keep the token out of exported or shared collections.

## Security

Every endpoint except the spec needs the token of an administrator (others get 403). A token has the full power of
its user, so keep it in `.env` and revoke it from the HA profile if it leaks.

A POST that changes several fields runs them one after another. Missing entities are found before anything changes,
but if the device rejects a later field, the earlier ones stay applied.

With an `http://` address the token travels unencrypted on your network. That is common at home; use an `https://`
address, or rotate the token, if you do not trust the network.

A POST answers with the state read right after the change. The device reports its new value a moment later, so a
field you just set can still show the old value; read it again to confirm.
