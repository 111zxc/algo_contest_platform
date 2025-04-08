from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    PROJECT_NAME: str = "Content Service"

    DATABASE_URL: str = Field("12345", env="DATABASE_URL")

    KEYCLOAK_URL: str = Field("http://keycloak:8080", env="KEYCLOAK_URL")
    KEYCLOAK_REALM: str = Field("myrealm", env="KEYCLOAK_REALM")
    KEYCLOAK_CLIENT_ID: str = Field("myclient", env="KEYCLOAK_CLIENT_ID")
    KEYCLOAK_CLIENT_SECRET: str = Field("secret", env="KEYCLOAK_CLIENT_SECRET")

    KEYCLOAK_ADMIN: str = Field("admin", env="KEYCLOAK_ADMIN")
    KEYCLOAK_ADMIN_PASSWORD: str = Field("admin", env="KEYCLOAK_ADMIN_PASSWORD")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
