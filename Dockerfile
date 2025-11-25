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

# System dependencies for building Python packages
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    git \
    curl \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# UV configuration
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
    uv sync --no-install-project --dev

ENV PATH="/workspace/project/.venv/bin:$PATH" \
    PYTHONPATH="/workspace/project" \
    ENVIRONMENT=development

# =============================================================================
# Stage: prod - Production image for CI/CD
# =============================================================================
FROM uv AS prod

# Copy deps and install to /opt/venv
WORKDIR /tmp/build
COPY pyproject.toml uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv venv /opt/venv && \
    VIRTUAL_ENV=/opt/venv uv sync --locked --no-dev

# Environment: venv at /opt/venv, code will be mounted at /workspace/project
ENV VIRTUAL_ENV="/opt/venv" \
    PATH="/opt/venv/bin:$PATH" \
    PYTHONPATH="/workspace/project" \
    ENVIRONMENT=production

# Code gets mounted here at runtime
WORKDIR /workspace/project

CMD ["bash"]