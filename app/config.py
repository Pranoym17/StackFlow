from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    openai_api_key: str = ""
    openai_model: str = "gpt-4.1-mini"
    openai_postmortem_model: str = "gpt-4.1"

    slack_bot_token: str = ""
    slack_signing_secret: str = ""

    jira_base_url: str = ""
    jira_email: str = ""
    jira_api_token: str = ""
    jira_project_key: str = "OPS"

    confluence_base_url: str = ""
    confluence_email: str = ""
    confluence_api_token: str = ""
    confluence_space_id: str = ""

    pagerduty_routing_key: str = ""

    upstash_redis_rest_url: str = ""
    upstash_redis_rest_token: str = ""

    app_base_url: str = "http://localhost:8000"
    demo_mode: bool = Field(default=True)

    @property
    def redis_configured(self) -> bool:
        return bool(self.upstash_redis_rest_url and self.upstash_redis_rest_token)

    @property
    def jira_configured(self) -> bool:
        return bool(self.jira_base_url and self.jira_email and self.jira_api_token)

    @property
    def confluence_configured(self) -> bool:
        return bool(self.confluence_base_url and self.confluence_email and self.confluence_api_token)

    @property
    def slack_configured(self) -> bool:
        return bool(self.slack_bot_token)

    @property
    def pagerduty_configured(self) -> bool:
        return bool(self.pagerduty_routing_key)


@lru_cache
def get_settings() -> Settings:
    return Settings()
