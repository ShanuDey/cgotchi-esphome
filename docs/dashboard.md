# Home Assistant dashboard

A ready-made control dashboard for the device: speaker, display, clock, face
(expression, frame rate, theme and colors), motion and touch, voice assistant,
message screen, WebView and Display Frame, plus a mic level graph.
Config: [../dashboard/cgotchi-control.yaml](../dashboard/cgotchi-control.yaml).

It holds no secrets: only entity IDs and card settings. The WebView and Display
Frame addresses are entity values that stay in your own Home Assistant.

## Install

1. In HACS, install these Frontend cards: **Mushroom** (piitaya/lovelace-mushroom),
   **layout-card** (thomasloven/lovelace-layout-card) and **card-mod**
   (thomasloven/lovelace-card-mod).
2. **Settings > Dashboards > Add dashboard > New dashboard from scratch**.
   Name it, for example, "cgotchi control".
3. Open it, then the three dots, **Edit dashboard**, three dots again,
   **Raw configuration editor**.
4. Replace everything with the contents of `cgotchi-control.yaml` and save.

## Entity names

The file uses `cgotchi_` in every entity ID, which is what the device name
`cgotchi` gives (for example `select.cgotchi_display_page`).

Home Assistant builds an entity ID from the device name when the entity is first
added. Renaming the device later only renames IDs that matched the old name, so
a device adopted under another name, or placed in an area, can keep IDs such as
`<area>_<name>_...`.

To check yours, open **Settings > Devices > cgotchi**, click an entity, then the
gear icon and read its **Entity ID**. If it differs, either edit the IDs there,
or in the raw editor use **Find and replace** (Ctrl+H) to change `cgotchi_` to
your prefix. The full list of entities is in [ha-entities.md](ha-entities.md).

## Notes

- Text boxes (Message, WebView URL, Display Frame URL) are Mushroom cards: tap
  one to edit it in the pop-up.
- The Mic level graph is mostly empty: the sensor only measures while the voice
  assistant is capturing.
- "Entity not found" on a card means no entity has that ID: the prefix differs
  (see above), or the entity was renamed or removed since you pasted the YAML.
  HA keeps its own copy, so re-paste after the file changes. "Unavailable"
  means the device is offline.
- The Shake and Face touch cards show the latest event, not a live state. Face
  touch shows `-` until the first touch after a restart.
