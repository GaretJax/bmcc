requirements.txt: requirements.in
	docker compose build deps
	docker compose run deps

test:
	docker compose run test pytest bmcc

lint:
	docker run -u 1000:1000 --rm --env-file=.env-local -v $(CURDIR):/app divio/lint /bin/lint ${ARGS}

lint_pre_commit:
	docker run -u 1000:1000 --rm --env-file=.env-local -v $(CURDIR):/app divio/lint /bin/lint --check --staged ${ARGS}
