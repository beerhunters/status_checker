from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from typing import Literal


class Settings(BaseSettings):
    bot_token: str = Field(..., env="BOT_TOKEN")
    db_name: str = Field("/app/data/monitoring_bot.db", env="DB_NAME")
    check_interval_minutes: int = Field(5, env="CHECK_INTERVAL_MINUTES")
    admin_username: str = Field("admin", env="ADMIN_USERNAME")
    admin_password: str = Field("strongpassword", env="ADMIN_PASSWORD")
    admin_chat_id: int = Field(..., env="ADMIN_CHAT_ID")
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        "INFO", env="LOG_LEVEL"
    )
    jwt_secret_key: str = Field("your-secure-random-key-here", env="JWT_SECRET_KEY")

    @property
    def database_url_async(self) -> str:
        return f"sqlite+aiosqlite:///{self.db_name}"

    @property
    def database_url_sync(self) -> str:
        return f"sqlite:///{self.db_name}"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
