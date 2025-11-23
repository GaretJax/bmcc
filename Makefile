reqs:
	docker compose build deps
	docker compose run --remove-orphans deps

test:
	docker compose run --remove-orphans test pytest bmcc

lint:
	docker compose run --remove-orphans lint

lint_pre_commit:
	docker compose run -T --remove-orphans lint --check --staged ${ARGS}
