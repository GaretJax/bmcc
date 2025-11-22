reqs:
	docker compose build deps
	docker compose run deps

test:
	docker compose run test pytest bmcc

lint:
	docker compose run lint

lint_pre_commit:
	docker compose run lint --check --staged ${ARGS}
