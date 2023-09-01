SHELL := /bin/bash
.PHONY: help format install lint test release

help:
	@grep '^\.PHONY' Makefile | cut -d' ' -f2- | tr ' ' '\n'

format:
	isort --profile black .
	black .

install:
	pip install -e .[dev]

lint:
	isort --profile black -c --diff .
	black --check .
	flake8 .

test:
	pytest --cov=pip_abandoned --cov-report term --cov-report xml ./tests

release:
	# usage: `make release version=0.0.0`
	make test
	@echo ""
	make lint
	@echo ""
	./release.sh "$(version)"
