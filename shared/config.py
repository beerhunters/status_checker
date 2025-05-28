# shared/config.py
from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Literal
from shared.logger_setup import logger
import os

# Загружаем переменные из .env файла, если он существует
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseSettings):
    bot_token: str = Field(..., env="BOT_TOKEN")
    db_user: str = Field("postgres", env="DB_USER")
    db_password: str = Field("mysecretpassword", env="DB_PASSWORD")
    db_host: str = Field("db", env="DB_HOST")
    db_port: int = Field(5432, env="DB_PORT")
    db_name: str = Field("monitoring_bot", env="DB_NAME")
    redis_host: str = Field("redis", env="REDIS_HOST")
    redis_port: int = Field(6379, env="REDIS_PORT")
    redis_db: int = 0
    check_interval_minutes: int = Field(5, env="CHECK_INTERVAL_MINUTES")
    admin_username: str = Field("admin", env="ADMIN_USERNAME")
    admin_password: str = Field("strongpassword", env="ADMIN_PASSWORD")
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        "INFO", env="LOG_LEVEL"
    )
    jwt_secret_key: str = Field("your-secure-random-key-here", env="JWT_SECRET_KEY")
    # sqlalchemy_echo: bool = False

    @property
    def database_url_async(self) -> str:
        """Асинхронный URL для SQLAlchemy (asyncpg)."""
        return f"postgresql+asyncpg://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"

    @property
    def database_url_sync(self) -> str:
        """Синхронный URL для SQLAlchemy (psycopg2)."""
        return f"postgresql+psycopg2://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"

    @property
    def redis_url(self) -> str:
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
logger.debug(f"Loaded settings (DB_HOST: {settings.db_host})")
