SHELL := /bin/bash

.PHONY: help setup run doctor test

help:
	@printf '%s\n' \
		"Available targets:" \
		"  make setup         - prepare local environment" \
		"  make run           - prepare local environment and start the app" \
		"  make doctor        - run doctor with dependency bootstrap" \
		"  make test          - run the full project test suite"

setup:
	bash ./setup_local.sh

run:
	bash ./run_local.sh

doctor:
	bash ./doctor

test:
	bash ./doctor --ci all
