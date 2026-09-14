from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routes import parties, stats, status

app = FastAPI(
    title="TableTurn API",
    description="Single-restaurant waitlist manager backend. See /_docs/specs.md and /openapi.yaml.",
    version="0.1.0",
)

# Wide open for local dev against the Vite frontend; tighten once deployed.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(parties.router)
app.include_router(stats.router)
app.include_router(status.router)


@app.get("/health", tags=["health"])
def health() -> dict:
    return {"status": "ok"}
