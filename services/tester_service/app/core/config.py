from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",  # чтобы лишние env не валили загрузку
    )

    PROJECT_NAME: str = "Tester Service"

    DATABASE_URL: str = "sqlite:///tester.db"

    KEYCLOAK_URL: str = "http://keycloak:8080"
    KEYCLOAK_REALM: str = "myrealm"
    KEYCLOAK_CLIENT_ID: str = "myclient"
    KEYCLOAK_CLIENT_SECRET: str = "secret"

    DOCKER_HOST: str = "tcp://dind:2375"

    CONTENT_SERVICE_URL: str = "http://content_service:8000"

    CELERY_BROKER_URL: str = "amqp://guest:guest@rabbitmq:5672"

    LANGUAGES_CONFIG: str = "languages.yaml"


settings = Settings()
