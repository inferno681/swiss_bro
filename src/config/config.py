from pathlib import Path

import yaml
from pydantic import BaseModel, Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class ServiceSettings(BaseModel):
    """Service settings."""

    webhook: bool
    web_server_host: str
    web_server_port: int
    webhook_path: str
    base_webhook_url: str
    page_size: int
    goto_timeout: int
    wait_timeout: int
    currency_rate_source: str
    rate_data_ttl: int
    admins: list[int]
    locales: list[str]


class MongoSettings(BaseModel):
    """MongoDB settings."""

    host: str
    port: int
    db: str


class Secrets(BaseSettings):
    """Secrets settings."""

    bot_token: SecretStr = Field(default=SecretStr('token'), alias='BOT_TOKEN')
    webhook_secret: SecretStr = Field(
        default=SecretStr('secret'), alias='WEBHOOK_SECRET'
    )
    mongo_user: SecretStr = Field(
        default=SecretStr('user'), alias='MONGO_INITDB_ROOT_USERNAME'
    )
    mongo_password: SecretStr = Field(
        default=SecretStr('password'), alias='MONGO_INITDB_ROOT_PASSWORD'
    )

    model_config = SettingsConfigDict(
        env_file='.env', env_file_encoding='utf-8'
    )


class AppConfig(BaseSettings):
    """Main configuration class."""

    service: ServiceSettings
    mongodb: MongoSettings
    secrets: Secrets

    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        case_sensitive=False,
        extra='allow',
    )

    @classmethod
    def load_settings(cls, file_path: str) -> 'AppConfig':
        """Load configuration from YAML and environment variables."""
        yaml_config = yaml.safe_load(
            Path(file_path).read_text(encoding='utf-8')
        )
        return cls(**yaml_config, secrets=Secrets())

    @property
    def mongo_url(self):
        """Mongo URL."""
        return (
            f'mongodb+srv://{self.secrets.mongo_user.get_secret_value()}:'
            f'{self.secrets.mongo_password.get_secret_value()}@'
            f'{self.mongodb.host}/'
        )

    @property
    def webhook_url(self):
        """Webhook url."""
        return f'{self.service.base_webhook_url}{self.service.webhook_path}'


config = AppConfig.load_settings('src/config/config.yaml')
