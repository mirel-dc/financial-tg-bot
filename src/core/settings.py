from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    
    # Telegram Bot
    bot_token: str = Field(..., env="BOT_TOKEN")


    # Database
    db_url: str = Field(..., alias="DB_URL")


    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False, extra="allow")


def get_settings() -> Settings:
    return Settings()