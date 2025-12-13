FROM python:3.11-slim

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    LANG=C.UTF-8

# system deps (ffmpeg required by whisper; libsndfile required by torchaudio)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
      ffmpeg \
      libsndfile1 \
      build-essential \
      ca-certificates \
      git && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install CPU-only PyTorch wheels + torchaudio, then openai-whisper.
# If you want reproducible builds put these in requirements.txt and pin exact versions.
RUN pip install --no-cache-dir \
      --index-url https://download.pytorch.org/whl/cpu \
      "torch==2.7.1" "torchaudio==2.7.1" && \
    pip install --no-cache-dir openai-whisper

# copy your transcribe script
COPY transcribe.py /app/transcribe.py

VOLUME [ "/audio", "/root/.cache/whisper" ]
ENTRYPOINT ["python", "/app/transcribe.py"]

