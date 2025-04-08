# Use an official Python runtime as a parent image
# Use a multi-arch compatible base image
FROM --platform=$TARGETPLATFORM python:3.9-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    POETRY_VERSION=1.6.1 \
    POETRY_HOME="/opt/poetry" \
    POETRY_VIRTUALENVS_CREATE=false \
    POETRY_NO_INTERACTION=1 \
    VIRTUAL_ENV="/opt/venv"

# Support for multi-arch builds
ARG TARGETPLATFORM
ARG BUILDPLATFORM

# Set the working directory in the container
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN curl -sSL https://install.python-poetry.org | python3 -

# Add Poetry to PATH
ENV PATH="${POETRY_HOME}/bin:${PATH}"

# Create a non-root user
RUN adduser --disabled-password --gecos "" appuser && \
    mkdir -p /app/data && \
    chown -R appuser:appuser /app

# Copy only dependency files first to leverage Docker cache
COPY --chown=appuser:appuser pyproject.toml poetry.lock* ./

# Set up virtual environment
RUN python -m venv ${VIRTUAL_ENV} && \
    . ${VIRTUAL_ENV}/bin/activate && \
    pip install --upgrade pip && \
    poetry install --no-interaction --no-dev

# Copy the rest of the application
COPY --chown=appuser:appuser . .

# Switch to non-root user
USER appuser

# Expose the port the app runs on
EXPOSE 8001

# Command to run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]
