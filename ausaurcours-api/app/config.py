from functools import lru_cache
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    # App
    ENV: str = Field(default="production")
    SITE_NAME: str = Field(default="Au SAURcours !")
    ALLOWED_ORIGINS: str = Field(default="*")

    # DB
    DB_HOST: str
    DB_PORT: int = 3306
    DB_NAME: str
    DB_USER: str
    DB_PASSWORD: str
    # Admin (Back-office) via X-Admin-Token
    ADMIN_TOKEN: str = Field(default="CHANGE_ME_ADMIN")

    # Typesense
    TYPESENSE_PROTOCOL: str = "http"
    TYPESENSE_HOST: str = "127.0.0.1"
    TYPESENSE_PORT: int = 8108
    TYPESENSE_API_KEY: str = ""
    TYPESENSE_COLLECTION: str = "articles"

    # JWT (front éditeur)
    JWT_SECRET: str = Field(default="CHANGE_ME_LONG_AND_RANDOM")
    JWT_ALGORITHM: str = Field(default="HS256")
    JWT_EXPIRE_MINUTES: int = Field(default=480)

    class Config:
        env_file = ".env"
        extra = "ignore"


@lru_cache
def get_settings() -> Settings:
    return Settings()
