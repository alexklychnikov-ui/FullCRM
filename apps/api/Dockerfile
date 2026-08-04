FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

ARG APP_UID=10001
ARG APP_GID=10001

WORKDIR /app

COPY pyproject.toml ./
COPY app ./app
COPY alembic.ini ./
COPY migrations ./migrations
COPY docker-entrypoint.sh ./docker-entrypoint.sh

RUN python -m pip install --upgrade pip && \
    python -m pip install . && \
    groupadd --system --gid ${APP_GID} fullcrm && \
    useradd --system --uid ${APP_UID} --gid fullcrm --create-home --home-dir /home/fullcrm fullcrm && \
    sed -i 's/\r$//' /app/docker-entrypoint.sh && \
    chmod +x /app/docker-entrypoint.sh && \
    chown -R fullcrm:fullcrm /app

USER fullcrm:fullcrm

EXPOSE 8000

ENTRYPOINT ["/app/docker-entrypoint.sh"]
