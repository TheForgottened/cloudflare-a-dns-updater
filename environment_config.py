from functools import lru_cache

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class EnvironmentConfig(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="cf_dns_updater_", extra="ignore")

    api_token: SecretStr
    zone_name: str


@lru_cache
def get_env_config() -> EnvironmentConfig:
    return EnvironmentConfig()
