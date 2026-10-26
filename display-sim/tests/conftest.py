import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))   # so "simctl" imports like control.py's

from simctl.app import create_app
from simctl.config import SETTINGS_EXAMPLE_PATH
from simctl.face_headers import load_meta
from simctl.launcher import Simulator
from simctl.settings_file import SettingsFile


@pytest.fixture
def meta():
    return load_meta()


@pytest.fixture
def settings_file(meta, tmp_path):
    return SettingsFile(meta, path=tmp_path / "settings.txt", example=SETTINGS_EXAMPLE_PATH)


@pytest.fixture
def client(meta, settings_file):
    simulator = Simulator(managed=False)
    with TestClient(create_app(meta, settings_file, simulator)) as client:
        yield client
