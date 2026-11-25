# ---- build stage: compiles/installs dependencies (build tools stay here) ----
FROM python:3.12.16-slim-bookworm AS builder
ENV PIP_NO_CACHE_DIR=1 PIP_DISABLE_PIP_VERSION_CHECK=1
WORKDIR /build
# manifest first => dependency layer is cached until requirements change
COPY app/requirements.txt .
RUN python -m venv /opt/venv && /opt/venv/bin/pip install -r requirements.txt

# ---- runtime stage: no pip cache, no compilers ----
FROM python:3.12.16-slim-bookworm
ARG APP_VERSION=dev
ARG FAIL_HEALTH=0
ENV PATH=/opt/venv/bin:$PATH \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    APP_VERSION=${APP_VERSION} \
    FAIL_HEALTH=${FAIL_HEALTH} \
    PORT=8000
RUN groupadd --system app && useradd --system --gid app --no-create-home app
COPY --from=builder /opt/venv /opt/venv
WORKDIR /srv
COPY --chown=app:app app/app.py .
USER app
EXPOSE 8000
HEALTHCHECK --interval=15s --timeout=3s --start-period=10s --retries=3 \
  CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/health').status==200 else 1)"
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "2", "app:app"]
