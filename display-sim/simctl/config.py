"""Where things live on disk."""
from pathlib import Path

SIM_DIR = Path(__file__).resolve().parents[1]            # display-sim
FACE_DIR = SIM_DIR.parent / "components" / "face"        # components/face
SETTINGS_PATH = SIM_DIR / "settings.txt"
SETTINGS_EXAMPLE_PATH = SIM_DIR / "settings.example.txt"
WEB_DIR = SIM_DIR / "web"
