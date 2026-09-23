from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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
