# syntax=docker/dockerfile:1

# ---------------------------------------------------------------------------
# Stage 1 — build the frontend with Node.
# Produces the static SPA bundle in /frontend/dist, copied into the runtime
# image below.
# ---------------------------------------------------------------------------
FROM node:22-alpine AS frontend

WORKDIR /frontend

# Base URL the browser uses for API calls. Empty => same-origin relative URLs,
# which is what we want when the backend serves the frontend from one origin.
# (frontend/.env.production also defaults this to empty; the ARG lets a build
# override it, e.g. to point at a separately hosted API.)
ARG VITE_API_BASE_URL=""
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL

# Install dependencies first so this layer caches unless the lockfile changes.
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci

COPY frontend/ ./
RUN npm run build

# ---------------------------------------------------------------------------
# Stage 2 — Python runtime: backend + built frontend, served together.
# uv's image ships both uv and Python 3.12.
# ---------------------------------------------------------------------------
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim AS runtime

WORKDIR /app/backend

# uv settings: copy packages into the venv (no hardlinks across the mount) and
# use the interpreter already in the image rather than downloading one.
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never \
    PATH="/app/backend/.venv/bin:$PATH"

# Install dependencies first (without the project) for a cached layer that only
# busts when the lockfile or manifest changes.
COPY backend/pyproject.toml backend/uv.lock backend/.python-version backend/README.md ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-install-project --no-dev

# Now the source, then install the project itself into the venv.
COPY backend/src ./src
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev

# Built frontend from stage 1; FRONTEND_DIST switches on static serving in
# backend/main.py.
COPY --from=frontend /frontend/dist /app/frontend/dist
ENV FRONTEND_DIST=/app/frontend/dist

# The container's port. Render/most PaaS inject $PORT; default to 8000 locally.
ENV PORT=8000
EXPOSE 8000

# Shell form so $PORT expands at runtime.
CMD uvicorn backend.main:app --host 0.0.0.0 --port ${PORT}
