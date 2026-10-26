# syntax=docker/dockerfile:1
# LearnLoop - one image serves the API and the built React UI.
#
#   docker build -t learnloop .                 # runtime image (default target)
#   docker build --target test -t learnloop-test .  # node + python + dev deps for the test suite

ARG PYTHON_IMAGE=python:3.12-slim
ARG NODE_IMAGE=node:22-bookworm-slim
ARG UV_IMAGE=ghcr.io/astral-sh/uv:0.11

FROM ${UV_IMAGE} AS uv

# ---------- 1. build the frontend ----------
FROM ${NODE_IMAGE} AS frontend-build
WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY frontend/ ./
# Same-origin API in the container: the UI calls /api on the FastAPI host.
ENV VITE_API_BASE_URL=""
RUN npm run build

# ---------- 2. backend dependencies ----------
FROM ${PYTHON_IMAGE} AS backend-deps
COPY --from=uv /uv /bin/uv
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy UV_PYTHON_DOWNLOADS=never
WORKDIR /app/backend
COPY backend/pyproject.toml backend/uv.lock backend/README.md ./
RUN uv sync --frozen --no-dev --no-install-project
COPY backend/src ./src
RUN uv sync --frozen --no-dev

# ---------- 3. runtime (default target, deployed to Render) ----------
FROM ${PYTHON_IMAGE} AS runtime
ARG APP_VERSION=dev
ENV APP_VERSION=${APP_VERSION} \
    PYTHONUNBUFFERED=1 \
    PATH="/app/backend/.venv/bin:${PATH}" \
    STATIC_DIR=/app/static \
    PORT=8000
RUN useradd --create-home --uid 10001 learnloop
WORKDIR /app/backend
COPY --from=backend-deps --chown=learnloop:learnloop /app/backend /app/backend
COPY --from=frontend-build --chown=learnloop:learnloop /app/frontend/dist /app/static
USER learnloop
EXPOSE 8000
HEALTHCHECK --interval=15s --timeout=5s --start-period=15s --retries=3 \
  CMD python -c "import os,urllib.request; urllib.request.urlopen(f'http://127.0.0.1:{os.environ.get(\"PORT\",\"8000\")}/health', timeout=4)"
# sh -c so $PORT (set by Render) is expanded at start-up.
CMD ["sh", "-c", "exec uvicorn learnloop.main:app --host 0.0.0.0 --port ${PORT:-8000} --no-access-log --proxy-headers --forwarded-allow-ips='*'"]

# ---------- 4. test image: node + uv-managed python, all dev deps ----------
FROM ${NODE_IMAGE} AS test
COPY --from=uv /uv /bin/uv
ENV UV_LINK_MODE=copy UV_PYTHON=3.12 UV_PYTHON_DOWNLOADS=automatic TELEMETRY_EXPORTER=none
WORKDIR /app
COPY backend/pyproject.toml backend/uv.lock backend/README.md ./backend/
RUN cd backend && uv sync --frozen --no-install-project
COPY frontend/package.json frontend/package-lock.json ./frontend/
RUN cd frontend && npm ci --no-audit --no-fund
COPY . .
RUN cd backend && uv sync --frozen
CMD ["sh", "scripts/run-tests.sh"]
