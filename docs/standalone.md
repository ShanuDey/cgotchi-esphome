# Use without Home Assistant

The face, touch and motion reactions, volume buttons, themes and the Message and Clock pages run on the device. Voice,
the Display Frame and WebView pages, and anything that needs Home Assistant or your servers do not work without a network.

## Control it from a phone

1. If the device cannot join your Wi-Fi, it starts its own hotspot, **Cgotchi Fallback**, after about 90 seconds. Join it
   with the `ap_password` from `secrets.yaml`. iOS shows a "No Internet" Wi-Fi setup sheet: close it and stay connected.
2. Open `http://192.168.4.1/time` in the browser. It sends the phone's clock to the device, then opens the controls.
   Bookmark it. On a network, use the device's IP instead of `192.168.4.1`.
3. Use the controls page for the face, page, theme, volume and message.

The time is kept in RAM only, so open `/time` again after the device restarts. When Home Assistant is connected it sets
the clock itself and the manual time is not used.

## Notes

- The page is served from the device (`web_server` with `local: true`), so it works with no internet.
- There is no login on the page or its REST API (`POST /select/Display%20Page/set?option=Clock`). Anyone on the same
  network can use it. The hotspot is protected by its password.
- The `/update` firmware upload on the page is off (`ota: false`). Flash with ESPHome as usual.
- `api` and `wifi` have `reboot_timeout: 0s`, so the device stays up with no Home Assistant or router.
