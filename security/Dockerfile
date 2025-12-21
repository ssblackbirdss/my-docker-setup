# syntax=docker/dockerfile:1
ARG BASE_IMAGE=python:3.11-slim
ARG USER_ID=1000
ARG GROUP_ID=1000

########################################
# builder: install deps and build wheel / collect static files
########################################

FROM ${BASE_IMAGE} AS builder
ARG USER_ID
ARG GROUP_ID
ENV HOME=/home/blackbird
RUN groupadd --gid ${GROUP_ID} blackbird \
 && useradd --uid ${USER_ID} --gid ${GROUP_ID} --create-home --home-dir /home/blackbird --shell /usr/sbin/nologin blackbird \
 && mkdir -p /home/blackbird && chown -R ${USER_ID}:${GROUP_ID} /home/blackbird && chmod 700 /home/blackbird

WORKDIR /home/blackbird
COPY --chown=${USER_ID}:${GROUP_ID} pyproject.toml poetry.lock* ./
RUN pip install --upgrade pip setuptools wheel


COPY --chown=${USER_ID}:${GROUP_ID} . .
USER ${USER_ID}
RUN pip install --prefix=/home/blackbird/.local -r requirements.txt \
 && python -m compileall .

########################################
# runtime: distroless python
########################################

FROM gcr.io/distroless/python3:3.11
ARG USER_ID=1000
ARG GROUP_ID=1000
WORKDIR /home/blackbird

COPY --from=builder --chown=${USER_ID}:${GROUP_ID} /home/blackbird /home/blackbird
USER ${USER_ID}

CMD ["./app.py"]   # Replace with your Python entrypoint, e.g. ["-m","myservice"]
