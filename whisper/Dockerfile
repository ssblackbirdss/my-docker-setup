# syntax=docker/dockerfile:1.4
FROM python:3.11-slim

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    LANG=C.UTF-8 \
    WHISPER_MODEL=small \
    WHISPER_LANGUAGE=""

WORKDIR /app

# 1) Install system packages (rarely change)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
      ffmpeg \
      libsndfile1 \
      build-essential \
      ca-certificates \
      git && \
    rm -rf /var/lib/apt/lists/*

# 2) Copy requirements and install Python deps (this layer is cached unless requirements.txt changes)
COPY requirements.txt /tmp/requirements.txt

# Use BuildKit cache for pip wheel downloads (fast subsequent builds).
# If BuildKit is not enabled, the mount line will be ignored.
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --no-cache-dir \
      --extra-index-url https://download.pytorch.org/whl/cpu \
      -r /tmp/requirements.txt

RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --no-cache-dir openai-whisper

# 3) Copy application files last so changes to code don't bust the pip install layer
COPY transcribe.py /app/transcribe.py
# COPY other app files if you have them (keep minimal to maximize cache hits)
# COPY src/ /app/src/

# Make audio and whisper cache dirs (these will typically be host-mounted at runtime)
RUN mkdir -p /audio /root/.cache/whisper

VOLUME [ "/audio", "/root/.cache/whisper" ]

ENTRYPOINT ["python", "/app/transcribe.py"]
