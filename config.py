import os
from os import environ as env

from dotenv import load_dotenv
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
TIMER_INTERVAL = int(os.getenv("TIMER_INTERVAL", 3600))
TELEGRAM_CHANNEL_ID = os.getenv("TELEGRAM_CHANNEL_ID", 0)
CURRENT_TOPIC=""




class DbConfig(BaseModel):
    DB_ECHO: bool = False

    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    POSTGRES_PORT: int = 5433
    POSTGRES_HOST: str = "localhost"

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@"
            f"{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )
    


class SchedulerConfig(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    SCHEDULER_ENABLED: bool = True
    SCHEDULER_INTERVAL_SECONDS: int = 15
    SCHEDULER_TIMEZONE: str = "UTC"
    
class Config(BaseModel):
    database: DbConfig = Field(default_factory=lambda: DbConfig(**env))
    scheduler: SchedulerConfig = Field(default_factory=SchedulerConfig)

config = Config()