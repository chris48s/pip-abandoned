SHELL := /bin/bash
.PHONY: build help format install lint test release venv

help:
	@grep '^\.PHONY' Makefile | cut -d' ' -f2- | tr ' ' '\n'

venv:
	python3 -m venv .venv

format:
	source .venv/bin/activate && \
	isort --profile black . && \
	black .

install:
	python3 -m venv .venv
	source .venv/bin/activate && \
	pip install -e .[dev]

lint:
	source .venv/bin/activate && \
	isort --profile black -c --diff . && \
	black --check . && \
	flake8 .

test:
	source .venv/bin/activate && \
	pytest --cov=pip_abandoned --cov-report term --cov-report xml ./tests

build:
	source .venv/bin/activate && \
	flit build

release:
	# usage: `make release version=0.0.0`
	make test
	@echo ""
	make lint
	@echo ""
	source .venv/bin/activate && \
	./release.sh "$(version)"
