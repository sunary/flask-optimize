.PHONY: install install-dev test run clean build format help

PYTHON ?= python3
PIP ?= pip3

help:
	@echo "Flask-Optimize - Makefile targets"
	@echo ""
	@echo "  install      Install package and dependencies"
	@echo "  install-dev  Install with test dependencies"
	@echo "  test         Run tests"
	@echo "  run          Run demo app"
	@echo "  build        Build source distribution"
	@echo "  format       Format code with black"
	@echo "  clean        Remove build artifacts"

install:
	$(PIP) install -e .

install-dev:
	$(PIP) install -e ".[test]"

test:
	$(PYTHON) -m pytest tests/ -v

run:
	$(PYTHON) tests/run_app.py

build:
	$(PYTHON) setup.py sdist bdist_wheel

format:
	$(PIP) install black -q && $(PYTHON) -m black flask_optimize/ tests/

clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .eggs/
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
