"""The API endpoints: a thin layer over meta, the settings file and the simulator."""
from fastapi import APIRouter, HTTPException

from .deps import MetaDep, SettingsFileDep, SimulatorDep
from .models import MetaOut, RestartOut, Settings, option_problems

router = APIRouter(prefix="/api")


@router.get("/meta")
def read_meta(meta: MetaDep) -> MetaOut:
    """What can be set: expressions, voice states, colors, themes and the frame rate range."""
    return MetaOut.from_meta(meta)


@router.get("/state")
def read_state(settings_file: SettingsFileDep) -> Settings:
    """The current settings.txt, including hand edits."""
    return settings_file.read()


@router.put("/state")
def write_state(settings: Settings, meta: MetaDep, settings_file: SettingsFileDep) -> Settings:
    """Replaces settings.txt. The simulator applies it within a fraction of a second."""
    problems = option_problems(settings, meta)
    if problems:
        raise HTTPException(status_code=422, detail=problems)
    settings_file.write(settings)
    return settings


@router.post("/restart")
def restart(simulator: SimulatorDep) -> RestartOut:
    """Restarts the simulator, to pick up edits to the face component (looks.h and friends)."""
    if not simulator.managed:
        raise HTTPException(status_code=409, detail="The simulator was not started by control.py (--no-sim)")
    simulator.restart()
    return RestartOut(status="restarting")
