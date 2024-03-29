.PHONY: build clean tests

NAME		:= ghcr.io/clayman-micro/passport
VERSION		?= latest
NAMESPACE 	?= micro
HOST 		?= 0.0.0.0
PORT 		?= 5000

clean: clean-build clean-pyc clean-test

clean-build:
	rm -fr build/
	rm -fr dist/
	rm -fr .eggs/
	find . -name '*.egg-info' -exec rm -fr {} +
	find . -name '*.egg' -exec rm -f {} +

clean-pyc:
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +
	find . -name '__pycache__' -exec rm -fr {} +

clean-test:
	rm -fr .tox/
	rm -f .coverage
	rm -fr tests/coverage
	rm -f tests/coverage.xml

install: clean
	poetry install

format:
	poetry run ruff --select I --fix src/passport tests
	poetry run black src/passport tests

check_black:
	@echo Check project with Black formatter.
	poetry run black --check src/passport tests

check_mypy:
	@echo Check project with Mypy typechecker.
	poetry run mypy src/passport tests

check_ruff:
	@echo Check project with Ruff linter.
	poetry run ruff --show-source --no-fix src/passport tests

lint: check_black check_ruff check_mypy

run:
	poetry run python3 -m passport --debug server run --host=$(HOST) --port=$(PORT)

tests:
	poetry run pytest

build:
	docker build -t ${NAME} .
	docker tag ${NAME} ${NAME}:$(VERSION)

publish:
	docker login -u $(DOCKER_USER) -p $(DOCKER_PASS) ghcr.io
	docker push ${NAME}

deploy:
	helm upgrade passport ../helm-chart/charts/micro --install --force \
		--namespace ${NAMESPACE} \
		--set image.repository=${NAME} \
		--set image.pullPolicy=Always \
		--set image.tag=$(VERSION) \
		--set replicas=$(REPLICAS) \
		--set serviceAccount.name=micro \
		--set imagePullSecrets[0].name=ghcr \
		--set ingress.enabled=false \
		--set ingress.rules={"Host(\`$(DOMAIN)\`)"} \
		--set migrations.enabled=false \
		--set livenessProbe.enabled=true \
		--set readinessProbe.enabled=true
