from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8', extra='ignore')

    app_name: str = 'prospera-wallet'
    environment: str = 'dev'
    api_prefix: str = '/api/v1'

    database_url: str
    jwt_secret: str
    jwt_algorithm: str = 'HS256'
    jwt_exp_minutes: int = 120

    bot_token: str
    bot_webhook_secret: str = 'webhook-secret'
    bot_webhook_path: str = '/telegram/webhook'
    bot_webhook_url: str | None = None

    rate_limit_per_minute: int = 120
    allow_negative_balances: bool = False


@lru_cache
def get_settings() -> Settings:
    return Settings()
