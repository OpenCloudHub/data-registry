# syntax=docker/dockerfile:1
# =============================================================================
# Data Registry Pipelines - Multi-stage Dockerfile
# =============================================================================
#
# Stages:
#   - uv:   Base image with uv package manager and system dependencies
#   - dev:  Development environment with all dependencies (for devcontainer)
#   - prod: Production image for CI/CD pipeline execution (Ray-based)
#
# Usage:
#   Development:  docker build --target dev -t data-registry:dev .
#   Production:   docker build --target prod -t data-registry:prod .
#
# =============================================================================

# =============================================================================
# Build Arguments
# =============================================================================
ARG RAY_VERSION=2.51.0
ARG PYTHON_MAJOR=3
ARG PYTHON_MINOR=12
ARG DISTRO=bookworm
ARG RAY_PY_TAG=py${PYTHON_MAJOR}${PYTHON_MINOR}
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
    wget \
    ca-certificates \
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
# Stage: prod - Production image for CI/CD (Ray-based for RayJob)
# =============================================================================
ARG RAY_VERSION
ARG RAY_PY_TAG
FROM rayproject/ray:${RAY_VERSION}-${RAY_PY_TAG} AS prod

WORKDIR /workspace/project

# Switch to ray user for all operations
USER ray

# Copy UV binary from uv stage
COPY --from=uv /usr/local/bin/uv /usr/local/bin/uv

# Copy dependency files with proper ownership
COPY --chown=ray:ray pyproject.toml uv.lock ./

# Install dependencies with caching
RUN --mount=type=cache,target=/home/ray/.cache/uv,uid=1000,gid=1000 \
    uv sync --no-dev --no-install-project

# Copy entire project (pipelines, scripts, etc.)
COPY --chown=ray:ray . .

ENV VIRTUAL_ENV="/workspace/project/.venv" \
    PATH="/workspace/project/.venv/bin:$PATH" \
    PYTHONPATH="/workspace/project" \
    ENVIRONMENT=production
