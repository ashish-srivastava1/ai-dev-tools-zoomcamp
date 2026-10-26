"""FastAPI application factory. Serves the API and (in the container) the built UI."""

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from . import __version__
from .config import Config, get_config
from .db import Database
from .routes import dashboard, health, modules, sessions, settings, tracks
from .telemetry import logger, setup_telemetry


def create_app(config: Config | None = None, telemetry_mode: str | None = None) -> FastAPI:
    config = config or get_config()
    db = Database(config.database_url)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        db.create_all()
        logger.info("app started", extra={"app_env": config.app_env, "version": config.version})
        yield
        app.state.telemetry.shutdown()

    app = FastAPI(
        title="LearnLoop API",
        version=__version__,
        description="Personal learning dashboard. Contract: openapi.yaml",
        lifespan=lifespan,
    )
    app.state.config = config
    app.state.db = db

    for r in (health, tracks, modules, sessions, dashboard, settings):
        app.include_router(r.router)

    setup_telemetry(app, db.engine, telemetry_mode)

    if config.static_dir and Path(config.static_dir, "index.html").exists():
        _mount_ui(app, Path(config.static_dir))
    return app


def _mount_ui(app: FastAPI, static: Path) -> None:
    if (static / "assets").is_dir():
        app.mount("/assets", StaticFiles(directory=static / "assets"), name="assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    def spa(full_path: str):
        if full_path.startswith("api/"):
            raise HTTPException(status_code=404, detail="not found")
        candidate = (static / full_path).resolve()
        if full_path and candidate.is_file() and static.resolve() in candidate.parents:
            return FileResponse(candidate)
        return FileResponse(static / "index.html")


app = create_app()
