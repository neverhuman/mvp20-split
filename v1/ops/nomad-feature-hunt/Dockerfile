FROM python:3.12.11-slim-bookworm@sha256:519591d6871b7bc437060736b9f7456b8731f1499a57e22e6c285135ae657bf7

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

COPY requirements.lock /tmp/requirements.lock
RUN python -m pip install -r /tmp/requirements.lock \
    && rm /tmp/requirements.lock \
    && useradd --uid 65532 --no-create-home --shell /usr/sbin/nologin sandbox

USER 65532:65532
WORKDIR /work
