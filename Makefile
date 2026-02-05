
SHELL := /bin/sh

CONTENT_DIR := services/content_service
TESTER_DIR  := services/tester_service

PYTEST_DEFAULT := -q
COV_TARGET := app

.PHONY: help \
        test test-content test-tester \
        test-vv test-content-vv test-tester-vv \
        cov cov-content cov-tester \
        cov-html cov-html-content cov-html-tester \
        clean

help:
	@echo Targets:
	@echo   make test                - run unit tests in both services
	@echo   make test-content        - run tests only in content_service
	@echo   make test-tester         - run tests only in tester_service
	@echo   make test-vv             - run tests in both services (verbose)
	@echo   make cov                 - run tests + coverage (term-missing) in both services
	@echo   make cov-content         - coverage only in content_service
	@echo   make cov-tester          - coverage only in tester_service
	@echo   make cov-html            - generate HTML coverage reports in both services

# ------------------------
# Tests
# ------------------------

test:
	@$(MAKE) test-content
	@$(MAKE) test-tester

test-content:
	cd $(CONTENT_DIR) && poetry run pytest $(PYTEST_DEFAULT) tests

test-tester:
	cd $(TESTER_DIR) && poetry run pytest $(PYTEST_DEFAULT) tests

test-vv:
	@$(MAKE) test-content-vv
	@$(MAKE) test-tester-vv

test-content-vv:
	cd $(CONTENT_DIR) && poetry run pytest -vv tests

test-tester-vv:
	cd $(TESTER_DIR) && poetry run pytest -vv tests

# ------------------------
# Coverage
# ------------------------

cov:
	@$(MAKE) cov-content
	@$(MAKE) cov-tester

cov-content:
	cd $(CONTENT_DIR) && poetry run pytest -q --cov=$(COV_TARGET) --cov-report=term-missing tests

cov-tester:
	cd $(TESTER_DIR) && poetry run pytest -q --cov=$(COV_TARGET) --cov-report=term-missing tests

cov-html:
	@$(MAKE) cov-html-content
	@$(MAKE) cov-html-tester

cov-html-content:
	cd $(CONTENT_DIR) && poetry run pytest -q --cov=$(COV_TARGET) --cov-report=html tests

cov-html-tester:
	cd $(TESTER_DIR) && poetry run pytest -q --cov=$(COV_TARGET) --cov-report=html tests
