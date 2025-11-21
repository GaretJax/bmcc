ARG VIRTUAL_ENV="/opt/venv"


FROM python:3.13-slim-trixie AS builder

RUN apt-get update --fix-missing && apt-get install -y \
      build-essential \
      libcap2-bin \
      libpq-dev \
      pkg-config

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/


FROM builder AS venv
ARG VIRTUAL_ENV

ENV UV_PROJECT_ENVIRONMENT=$VIRTUAL_ENV
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --no-dev --locked --compile-bytecode --no-install-project --link-mode=copy


FROM python:3.13-slim-trixie
ARG VIRTUAL_ENV

# hadolint ignore=DL3008
RUN apt-get update \
 && apt-get install -y --no-install-recommends \
      libcap2-bin \
      gettext \
 && apt-get clean \
 && rm -rf /var/lib/apt/lists/*

ENV VIRTUAL_ENV="$VIRTUAL_ENV" \
    EXECUTION_MODE=run \
    PATH="$VIRTUAL_ENV/bin:$PATH" \
    DJANGO_SETTINGS_MODULE=bmcc.settings

COPY --from=venv $VIRTUAL_ENV $VIRTUAL_ENV

# Allow uvicorn and python to listen on port 80 even when not running as root
RUN setcap 'cap_net_bind_service=+ep' $VIRTUAL_ENV/bin/uvicorn
RUN setcap 'cap_net_bind_service=+ep' $(readlink -f $VIRTUAL_ENV/bin/python)

RUN useradd --create-home --user-group -u 1000 app

COPY . /app/
WORKDIR /app

RUN EXECUTION_MODE=build python manage.py compilemessages
RUN EXECUTION_MODE=build python manage.py collectstatic --noinput --clear

USER app:app

EXPOSE 80

CMD ["uvicorn "--host=0.0.0.0:80", "--lifespan=off", "--port=80", "bmcc.asgi:application"]
