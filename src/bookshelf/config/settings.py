from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="BOOKSHELF_",
        extra="ignore",
    )

    env: str = "development"
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    database_url: str = Field(
        default="postgresql+psycopg://bookshelf:bookshelf@localhost:5432/bookshelf"
    )

    aws_access_key_id: str = "minioadmin"
    aws_secret_access_key: str = "minioadmin"
    s3_endpoint_url: str = "http://localhost:9000"
    s3_region: str = "us-east-1"
    s3_bucket: str = "bookshelf-thumbnails"
    s3_secure: bool = False


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
