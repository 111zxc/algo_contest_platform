from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    PROJECT_NAME: str = Field("Tester Service", env="PROJECT_NAME")

    DATABASE_URL: str = Field("sqlite:///tester.db", env="DATABASE_URL")

    KEYCLOAK_URL: str = Field("http://keycloak:8080", env="KEYCLOAK_URL")
    KEYCLOAK_REALM: str = Field("myrealm", env="KEYCLOAK_REALM")
    KEYCLOAK_CLIENT_ID: str = Field("myclient", env="KEYCLOAK_CLIENT_ID")
    KEYCLOAK_CLIENT_SECRET: str = Field("secret", env="KEYCLOAK_CLIENT_SECRET")

    DOCKER_HOST: str = Field("tcp://dind:2375", env="DOCKER_HOST")

    CONTENT_SERVICE_URL: str = Field(
        "http://content_service:8000", env="CONTENT_SERVICE_URL"
    )

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
