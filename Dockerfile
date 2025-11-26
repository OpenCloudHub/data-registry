# syntax=docker/dockerfile:1
# =============================================================================
# Data Registry Pipelines - Multi-stage Dockerfile
# =============================================================================
#
# Stages:
#   - uv:   Base image with uv package manager and system dependencies
#   - dev:  Development environment with all dependencies (for devcontainer)
#   - prod: Production image for CI/CD pipeline execution
#
# Usage:
#   Development:  docker build --target dev -t data-registry:dev .
#   Production:   docker build --target prod -t data-registry:prod .
#
# Runtime (prod):
#   docker run --rm -v $(pwd):/workspace/project <image> bash -c 'dvc repro ...'
#
# =============================================================================

# =============================================================================
# Build Arguments
# =============================================================================
ARG PYTHON_MAJOR=3
ARG PYTHON_MINOR=12
ARG DISTRO=bookworm
ARG UV_PY_TAG=python${PYTHON_MAJOR}.${PYTHON_MINOR}-${DISTRO}

# =============================================================================
# Stage: uv - Base image with uv and system dependencies
# =============================================================================
FROM ghcr.io/astral-sh/uv:${UV_PY_TAG} AS uv

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    git \
    curl \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# =============================================================================
# Stage: dev - Development environment (for devcontainer)
# =============================================================================
FROM uv AS dev

WORKDIR /workspace/project
COPY pyproject.toml uv.lock ./

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --no-install-project

ENV PATH="/workspace/project/.venv/bin:$PATH" \
    ENVIRONMENT=development

# =============================================================================
# Stage: prod - Production image for CI/CD
# =============================================================================
FROM uv AS prod

# Install dependencies at /app (separate from code mount point)
WORKDIR /app
COPY pyproject.toml uv.lock ./

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-group dev

# Venv at /app/.venv, code mounts at /workspace/project
ENV PATH="/app/.venv/bin:$PATH" \
    ENVIRONMENT=production

WORKDIR /workspace/project

CMD ["bash"]