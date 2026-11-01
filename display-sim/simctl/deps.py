"""What the routes depend on. The app holds the instances; tests swap them with dependency_overrides."""
from typing import Annotated

from fastapi import Depends, Request

from .launcher import Simulator
from .meta import Meta
from .settings_file import SettingsFile


def get_meta(request: Request) -> Meta:
    return request.app.state.meta


def get_settings_file(request: Request) -> SettingsFile:
    return request.app.state.settings_file


def get_simulator(request: Request) -> Simulator:
    return request.app.state.simulator


MetaDep = Annotated[Meta, Depends(get_meta)]
SettingsFileDep = Annotated[SettingsFile, Depends(get_settings_file)]
SimulatorDep = Annotated[Simulator, Depends(get_simulator)]
