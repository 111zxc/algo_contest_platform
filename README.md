# algo_contest_platform

Платформа для проведения алгоритмических контестов (в духе LeetCode/Codeforces): задачи, контесты, отправки решений и автоматическая проверка кода.

[demo](https://drive.google.com/file/d/1TQxG2UOXatZCHUaR-tiadEH7BxdVIhF4/view?usp=sharing)

**Технологии:** FastAPI, SQLAlchemy, Alembic, PostgreSQL, RabbitMQ, Celery, Keycloak, React, Nginx, docker-in-docker.

## Архитектура

- **content_service** — backend для контента: пользователи, задачи, контесты, посты, комментарии, теги, блог, реакции.  
  БД: **content_postgres** (PostgreSQL)

- **tester_service** — сервис проверки решений: принимает пользовательские посылки, исполняет код в изоляции и выставляет вердикты решениям.    
  БД: **tester_postgres** (PostgreSQL)  
  Очередь: **rabbitmq**  
  Воркер: **tester_worker** (Celery)  
  Исполнение: **dind** (docker-in-docker)  

- **gateway** — Nginx reverse-proxy для проксирования запросов к бэкенду.

- **keycloak** — IAM/SSO.

## Быстрый старт

С make:

```bash
git clone https://github.com/111zxc/algo_contest_platform
cd algo_contest_platform

cp ./services/tester_service/.env.example ./services/tester_service/.env
cp ./services/content_service/.env.example ./services/content_service/.env

make up
```

Без make:

```bash
git clone https://github.com/111zxc/algo_contest_platform
cd algo_contest_platform

cp ./services/tester_service/.env.example ./services/tester_service/.env
cp ./services/content_service/.env.example ./services/content_service/.env

docker compose up -d --build
```

## Порты и сервисы

Основные:
- **Frontend**: http://localhost:3000
- **Gateway (Nginx)**: http://localhost:8081
- **content_service**: http://localhost:8000
- **tester_service**: http://localhost:8001
- **Keycloak**: http://localhost:8080 *(admin/admin, myrealm)*

RabbitMQ:
- **AMQP**: 5672
- **UI**: http://localhost:15672 *(guest/guest)*

PostgreSQL (локально):
- **content_db**: http://localhost:5432
- **tester_db**: http://localhost:5433

Observability:
- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3001 *(admin/admin)*
- **Elasticsearch**: http://localhost:9200
- **Kibana**: http://localhost:5601

## Тестирование

### Модульное тестирование

```bash
make test          # pytest both services
make test-content  # pytest content_service
make test-tester   # pytest tester_service
make test-vv       # pytest -vv both services

make cov           # coverage for both services
make cov-content   # coverage for content_service
make cov-tester    # coverage for tester_service
make cov-html      # html coverage report
```

### Интеграционное тестирование

tbd

### E2E тестирование

tbd

### Нагрузочное тестирование

tbd

## Observability

tbd
