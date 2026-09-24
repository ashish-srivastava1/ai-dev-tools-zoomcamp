import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .db import init_db
from .routes import parties, stats, status


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="TableTurn API",
    description="Single-restaurant waitlist manager backend. See /_docs/specs.md and /openapi.yaml.",
    version="0.1.0",
    lifespan=lifespan,
)

# Local dev, plus the Vercel-deployed frontend — its production domain and
# every preview-deployment subdomain both match *.vercel.app.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(parties.router)
app.include_router(stats.router)
app.include_router(status.router)


@app.get("/health", tags=["health"])
def health() -> dict:
    return {"status": "ok"}


# When FRONTEND_DIST points at a built frontend (the Docker image sets this),
# the backend also serves the single-page app so one container answers both the
# API and the UI. Left unset in local dev — Vite serves the frontend there — so
# nothing below runs and the test suite is unaffected.
_frontend_dist = os.getenv("FRONTEND_DIST")
if _frontend_dist and (_dist := Path(_frontend_dist)).is_dir():
    # Hashed build assets are immutable — mount them directly.
    app.mount("/assets", StaticFiles(directory=_dist / "assets"), name="assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    def serve_spa(full_path: str) -> FileResponse:
        # /api/* fell through the routers above, so it's a genuine 404 — don't
        # mask it with index.html.
        if full_path.startswith("api/"):
            raise HTTPException(status_code=404, detail="Not Found")
        # Serve real files (favicon.svg, icons.svg, ...) when they exist;
        # otherwise hand back index.html so client-side routes (/status) work.
        candidate = _dist / full_path
        if full_path and candidate.is_file():
            return FileResponse(candidate)
        return FileResponse(_dist / "index.html")
