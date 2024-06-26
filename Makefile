.PHONY: clean-pyc clean-build docs

open := $(shell { which xdg-open || which open; } 2>/dev/null)
python = python3

help:
	@echo "Please use \`make <target>' where <target> is one of"
	@echo "  clean-build   to remove build artifacts"
	@echo "  clean-pyc     to remove Python file artifacts"
	@echo "  lint          to check style with flake8"
	@echo "  test          to run tests quickly with the default Python"
	@echo "  testall       to run tests on every Python version with tox"
	@echo "  coverage      to check code coverage quickly with the default Python"
	@echo "  docs          to generate Sphinx HTML documentation, including API docs"
	@echo "  release       to package and upload a release"
	@echo "  sdist         to package"

clean: clean-build clean-pyc

clean-build:
	rm -fr build/
	rm -fr dist/
	rm -fr *.egg-info

clean-pyc:
	find . -name '*.pyc' -type f -exec rm -f {} +
	find . -name '*.pyo' -type f -exec rm -f {} +
	find . -name '*~' -type f -exec rm -f {} +
	find . -name '__pycache__' -type d -exec rm -rf {} +

lint:
	flake8 snimpy tests
	interrogate --fail-under 50 -v snimpy tests

test:
	$(python) -m pytest

test-all:
	tox

coverage:
	coverage run --source snimpy -m unittest discover -s tests
	coverage report -m
	coverage html
	$(open) htmlcov/index.html

docs:
	$(MAKE) -C docs clean
	$(MAKE) -C docs html
	$(open) docs/_build/html/index.html

release: clean
	$(python) -m build
	twine upload dist/*.tar.gz

sdist: clean
	$(python) -m build
	ls -l dist
