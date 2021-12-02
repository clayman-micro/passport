.PHONY: build clean clean-test clean-pyc clean-build
NAME := ghcr.io/clayman-micro/passport
VERSION ?= latest
HOST ?= 0.0.0.0
PORT ?= 5000


clean: clean-build clean-image clean-pyc clean-test

clean-build:
	rm -fr build/
	rm -fr dist/
	rm -fr .eggs/
	find . -name '*.egg-info' -exec rm -fr {} +
	find . -name '*.egg' -exec rm -f {} +

clean-image:
	docker images -qf dangling=true | xargs docker rmi

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

lint:
	poetry run flake8 passport tests
	poetry run mypy passport tests

run:
	poetry run python3 -m passport --debug --conf-dir=./conf server run --host=$(HOST) --port=$(PORT)

test:
	py.test

test-all:
	tox -- --pg-image=postgres:12-alpine

build:
	docker build -t ${NAME} .
	docker tag ${NAME} ${NAME}:$(VERSION)

publish: build
	docker login -u $(DOCKER_USER) -p $(DOCKER_PASS) ghcr.io
	docker push ${NAME}

deploy:
	docker run --rm -it -v ${PWD}:/github/workspace --workdir /github/workspace \
		-e PASSPORT_VERSION=$(VERSION) \
		-e VAULT_ADDR=$(VAULT_ADDR) \
		-e VAULT_ROLE_ID=$(VAULT_ROLE_ID) \
		-e VAULT_SECRET_ID=$(VAULT_SECRET_ID) \
		ghcr.io/clayman-micro/action-deploy:v2.0.0 -i ansible/inventory ansible/deploy.yml

