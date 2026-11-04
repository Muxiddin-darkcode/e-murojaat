import os
from typing import List, Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    BOT_TOKEN: str = Field(default="", description="Telegram Bot Token")
    DATABASE_URL: str = Field(
        default="sqlite+aiosqlite:///data/e_murojaat.db",
        description="Database URL (PostgreSQL or SQLite)"
    )
    REDIS_URL: Optional[str] = Field(default=None, description="Redis URL for FSM and caching")
    SUPER_ADMIN_ID: int = Field(default=0, description="Telegram ID of Super Administrator")
    DEKAN_ID: int = Field(default=0, description="Telegram ID of Dekan")
    TIMEZONE: str = Field(default="Asia/Tashkent", description="Timezone name")
    APP_ENV: str = Field(default="production", description="Application environment: development / production")
    LOG_LEVEL: str = Field(default="INFO", description="Log level")
    MAX_FILE_SIZE_MB: int = Field(default=20, description="Max allowed file size in MB")
    ALLOWED_EXTENSIONS: List[str] = Field(
        default=[".pdf", ".doc", ".docx", ".jpg", ".jpeg", ".png", ".mp4", ".xlsx", ".zip", ".txt"],
        description="Allowed file extensions"
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()

