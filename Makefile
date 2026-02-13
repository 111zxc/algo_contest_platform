
SHELL := /bin/sh

CONTENT_DIR := services/content_service
TESTER_DIR  := services/tester_service

PYTEST_DEFAULT := -q
COV_TARGET := app

.PHONY: help \
		up down build logs ps \
        migrate migrate-content migrate-tester \
        rev-content rev-tester \
        upgrade-content upgrade-tester \
        test test-content test-tester \
        test-vv test-content-vv test-tester-vv \
        cov cov-content cov-tester \
        cov-html cov-html-content cov-html-tester

help:
	help:
	@echo Targets:
	@echo
	@echo   make up                  - docker compose up -d --build
	@echo   make down                - docker compose down
	@echo   make build               - docker compose build
	@echo   make logs                - docker logs (tail=200)
	@echo   make ps                  - docker ps
	@echo
	@echo   make migrate             - run migrations for both DBs (content + tester) via migrator containers
	@echo   make migrate-content     - run content_service migrations (alembic upgrade head) in docker
	@echo   make migrate-tester      - run tester_service migrations (alembic upgrade head) in docker
	@echo
	@echo   make rev-content m="..." - autogenerate new alembic revision for content_service (local)
	@echo   make rev-tester  m="..." - autogenerate new alembic revision for tester_service (local)
	@echo   make upgrade-content     - apply content_service migrations locally (alembic upgrade head)
	@echo   make upgrade-tester      - apply tester_service migrations locally (alembic upgrade head)
	@echo
	@echo   make test                - run unit tests in both services
	@echo   make test-content        - run tests only in content_service
	@echo   make test-tester         - run tests only in tester_service
	@echo   make test-vv             - run tests in both services (verbose)
	@echo
	@echo   make cov                 - run tests + coverage in both services
	@echo   make cov-content         - coverage only in content_service
	@echo   make cov-tester          - coverage only in tester_service
	@echo   make cov-html            - generate HTML coverage reports in both services
	@echo   make cov-html-content    - HTML coverage only in content_service
	@echo   make cov-html-tester     - HTML coverage only in tester_service

# ------------------------
# Docker compose
# ------------------------

up:
	docker compose up -d --build

down:
	docker compose down

build:
	docker compose build

logs:
	docker compose logs -f --tail=200

ps:
	docker compose ps

# ------------------------
# Migrations (docker)
# ------------------------

migrate: migrate-content migrate-tester

migrate-content:
	docker compose run --rm content_migrate

migrate-tester:
	docker compose run --rm tester_migrate

# ------------------------
# Migrations (local)
# ------------------------

rev-content:
	cd $(CONTENT_DIR) && poetry run alembic revision --autogenerate -m "$(m)"

rev-tester:
	cd $(TESTER_DIR) && poetry run alembic revision --autogenerate -m "$(m)"

upgrade-content:
	cd $(CONTENT_DIR) && poetry run alembic upgrade head

upgrade-tester:
	cd $(TESTER_DIR) && poetry run alembic upgrade head

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
