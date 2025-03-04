from pydantic import BaseSettings, Field


class Settings(BaseSettings):
    PROJECT_NAME: str = "Content Service"

    DATABASE_URL: str = Field("12345", env="DATABASE_URL")

    KEYCLOAK_URL: str = Field("http://keycloak:8080", env="KEYCLOAK_URL")
    KEYCLOAK_REALM: str = Field("myrealm", env="KEYCLOAK_REALM")
    KEYCLOAK_CLIENT_ID: str = Field("myclient", env="KEYCLOAK_CLIENT_ID")
    KEYCLOAK_CLIENT_SECRET: str = Field("secret", env="KEYCLOAK_CLIENT_SECRET")

    KAFKA_BOOTSTRAP_SERVERS: str = Field("kafka:9092", env="KAFKA_BOOTSTRAP_SERVERS")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
