# Repository Guidelines

## Project Structure & Module Organization
- Application code lives in `bmcc/` (Django project). Key apps include `missions`, `tracking`, `owntracks`, `celery`, and shared helpers in `utils/`.
- Django settings and entrypoints: `bmcc/settings.py`, `bmcc/asgi.py`, `bmcc/wsgi.py`, `manage.py`.
- Frontend assets and templates: `bmcc/static/` and `bmcc/templates/`; localization strings in `bmcc/locale/`.
- CI/CD config sits in `.github/workflows/`; Docker setup in `Dockerfile.base`, `docker-compose.yml`, `Makefile`.
- Artifacts, coverage, and static build outputs are written to `.data/` and `/artifacts` mounts inside containers.

## Build, Test, and Development Commands
- `docker compose run web` — launch the dev server with live reload (uses `bmcc.asgi` on port 80 behind the local proxy).
- `make reqs` — rebuild dependency images and refresh the `uv` lock (uses the `deps` service).
- `make test` or `docker compose run --remove-orphans test pytest bmcc` — run pytest with the Django test settings (`.env-testing` is loaded).
- `make lint` — run the lint suite via the `lint` service (ruff, formatting checks).
- `make lint_pre_commit ARGS="--files <paths>"` — lint staged/targeted files locally before committing.

## Coding Style & Naming Conventions
- Python 3.13; keep line length at 79 characters (ruff config). Ruff ignores `S101`; otherwise follow default rules in `/presets/ruff.toml`.
- Import order enforced by isort sections defined in `pyproject.toml` (`DJANGO`, `FIRSTPARTY`, `PROJECT`, etc.).
- Django apps, modules, and files use `snake_case`; management commands and Celery tasks follow the same.
- Prefer explicit imports; add docstrings to new public functions/classes; keep settings/env usage centralized in `bmcc/settings.py`.

## Testing Guidelines
- Test runner: pytest with pytest-django; coverage configuration lives in `pyproject.toml` and writes to `/artifacts/coverage`.
- Place tests next to the relevant app in a `tests/` package (e.g., `bmcc/missions/tests/test_api.py`); name files `test_<module>.py` and use `integration` marker for slower, external calls.
- Run `pytest bmcc --reuse-db` locally to reuse the containerized database; add `-k <keyword>` to scope.

## Commit & Pull Request Guidelines
- Follow the existing short, prefixed style seen in history (`feat: ...`, `fix: ...`); keep messages imperative and focused.
- PRs should describe what changed, why, and how to validate (commands or URLs). Link issues/tasks; include screenshots for UI or admin-facing changes.
- Ensure lint and tests pass before requesting review; mention any intentionally skipped checks or flaky cases.

## Security & Configuration Tips
- Do not commit secrets; credentials come from `.env-local` and `.env-secrets` for dev, `.env-testing` for tests. Keep these files local.
- Services assume Docker volumes for Postgres, artifacts, and static files; avoid modifying `.data/` manually outside containers.
- Sentry is configured via environment; scrub sensitive data in logs and error messages.
