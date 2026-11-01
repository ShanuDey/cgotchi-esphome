"""Constants for the cgotchi integration."""

DOMAIN = "cgotchi"

PAGES = ["Face", "Clock", "Message", "Display Frame", "WebView"]
THEMES = [
    "Classic", "Midnight", "Bubblegum", "Forest", "Sunset", "Grape",
    "Ocean", "Lava", "Paper", "Mint", "Night", "Custom",
]
EXPRESSIONS = [
    "Happy", "Sad", "Sleepy", "Surprised", "Angry", "Laughing", "Confused",
    "Love", "Wink", "Dizzy", "Celebrating", "Worried", "Bored",
]
CLOCK_FORMATS = ["12 hour", "24 hour"]

# Display field -> (entity domain, entity name on the device).
DISPLAY_FIELDS = {
    "page": ("select", "Display Page"),
    "frame_source": ("select", "Display Frame Source"),
    "frame_url": ("text", "Display Frame URL"),
    "clock_format": ("select", "Clock Format"),
    "theme": ("select", "Theme"),
    "expression": ("select", "Face Expression"),
    "frame_rate": ("number", "Face Frame Rate"),
    "message_title": ("text", "Message Title"),
    "message_body": ("text", "Message Body"),
    "accent_color": ("light", "Accent Color"),
    "secondary_color": ("light", "Secondary Color"),
    "background_color": ("light", "Background Color"),
}

# Touch and motion entities: key -> (domain, entity name).
TOUCH_ENTITIES = {
    "face_touch": ("event", "Face Touch"),
    "shake": ("event", "Shake"),
    "moving": ("binary_sensor", "Moving"),
    "face_up": ("binary_sensor", "Face Up"),
    "face_down": ("binary_sensor", "Face Down"),
    "volume_up": ("binary_sensor", "Volume Up"),
    "volume_down": ("binary_sensor", "Volume Down"),
}
