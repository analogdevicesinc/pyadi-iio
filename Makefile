.ONESHELL:

BIN=venv/bin

.PHONY: clean clean-build clean-pyc help dev
.DEFAULT_GOAL := help

define BROWSER_PYSCRIPT
import os, webbrowser, sys

from urllib.request import pathname2url

webbrowser.open("file://" + pathname2url(os.path.abspath(sys.argv[1])))
endef
export BROWSER_PYSCRIPT

define PRINT_HELP_PYSCRIPT
import re, sys

for line in sys.stdin:
	match = re.match(r'^([a-zA-Z_-]+):.*?## (.*)$$', line)
	if match:
		target, help = match.groups()
		print("%-20s %s" % (target, help))
endef
export PRINT_HELP_PYSCRIPT

BROWSER := python -c "$$BROWSER_PYSCRIPT"

help:
	@python -c "$$PRINT_HELP_PYSCRIPT" < $(MAKEFILE_LIST)

clean: clean-build clean-pyc clean-test ## remove all build, test, coverage and Python artifacts

clean-build: ## remove build artifacts
	rm -fr build/
	rm -fr dist/
	rm -fr .eggs/
	find . -name '*.egg-info' -exec rm -fr {} +
	find . -name '*.egg' -exec rm -f {} +

clean-pyc: ## remove Python file artifacts
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +
	find . -name '__pycache__' -exec rm -fr {} +

tests: ## run tests
	$(BIN)/python -m pytest -vs -k 'not prod'

etests: ## run emulation tests
	$(BIN)/python -m pytest -vs --cov=adi --scan-verbose --adi-hw-map --emu -k 'not prod'

lint: ## format and lint code
	pre-commit run --all-files

dev: ## setup development environment
	virtualenv venv
	source venv/bin/activate
	python -m pip install -r requirements_dev.txt
	echo ""
	echo ""
	echo "---Run 'source venv/bin/activate' to activate the virtual environment.---"
