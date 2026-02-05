from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    PROJECT_NAME: str = "Content Service"

    DATABASE_URL: str = "12345"

    KEYCLOAK_URL: str = "http://keycloak:8080"
    KEYCLOAK_REALM: str = "myrealm"
    KEYCLOAK_CLIENT_ID: str = "myclient"
    KEYCLOAK_CLIENT_SECRET: str = "secret"

    KEYCLOAK_ADMIN: str = "admin"
    KEYCLOAK_ADMIN_PASSWORD: str = "admin"


settings = Settings()
