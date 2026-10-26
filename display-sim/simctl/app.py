"""Builds the FastAPI app: the API router, the static page, and the simulator's lifetime."""
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from .config import WEB_DIR
from .launcher import Simulator
from .meta import Meta
from .routes import router
from .settings_file import SettingsFile


def _readable(error: dict) -> str:
    """One validation error as "field: what is wrong"."""
    field = ".".join(str(part) for part in error["loc"] if part != "body")
    message = error["msg"].removeprefix("Value error, ")
    return f"{field}: {message}" if field else message


def create_app(meta: Meta, settings_file: SettingsFile, simulator: Simulator) -> FastAPI:
    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        settings_file.ensure()
        if simulator.managed:
            simulator.start()
        try:
            yield
        finally:
            simulator.stop()

    app = FastAPI(
        title="Display simulator control",
        docs_url="/api/docs",
        redoc_url=None,
        openapi_url="/api/openapi.json",
        lifespan=lifespan,
    )
    app.state.meta = meta
    app.state.settings_file = settings_file
    app.state.simulator = simulator

    @app.exception_handler(RequestValidationError)
    def invalid_request(request: Request, exc: RequestValidationError) -> JSONResponse:
        # The page shows "detail" as text, so keep it a list of strings like the other 422s.
        return JSONResponse(status_code=422, content={"detail": [_readable(e) for e in exc.errors()]})

    app.include_router(router)
    app.mount("/", StaticFiles(directory=WEB_DIR, html=True), name="web")
    return app
