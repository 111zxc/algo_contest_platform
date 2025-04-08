# Dockerfile
FROM python:3.12-slim

ENV POETRY_VERSION=1.5.1
# Добавляем Poetry в PATH (по умолчанию Poetry устанавливается в /root/.local/bin)
ENV PATH="/root/.local/bin:${PATH}"

# Устанавливаем необходимые пакеты для сборки и curl для установки Poetry
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential curl && rm -rf /var/lib/apt/lists/*

# Устанавливаем Poetry
RUN curl -sSL https://install.python-poetry.org | python3 - --version $POETRY_VERSION

WORKDIR /app

# Копируем файлы для установки зависимостей
COPY pyproject.toml poetry.lock* /app/

# Отключаем создание виртуального окружения и устанавливаем зависимости
RUN poetry config virtualenvs.create false \
    && poetry install --no-root --only main

# Копируем исходный код проекта
COPY . /app/

EXPOSE 8000

# Запускаем приложение с помощью Uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
