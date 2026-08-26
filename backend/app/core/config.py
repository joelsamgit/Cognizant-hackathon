from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Plant Guardian API"
    app_env: str = "development"
    api_prefix: str = "/api"
    database_url: str = Field(min_length=1)
    cors_origins: str = "http://localhost:3000"
    auto_seed: bool = False
    vapid_public_key: str = ""
    vapid_private_key: str = ""
    vapid_subject: str = "mailto:admin@example.com"
    notification_dispatch_token: str = ""
    gcp_project_id: str = ""
    pubsub_notification_topic: str = ""
    pubsub_push_service_account: str = ""
    pubsub_push_audience: str = ""
    scheduler_service_account: str = ""
    scheduler_audience: str = ""
    session_lifetime_days: int = Field(default=7, ge=1, le=90)
    seed_starter_plants: bool = False
    google_client_id: str = ""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def notifications_enabled(self) -> bool:
        return bool(self.vapid_public_key and self.vapid_private_key and self.vapid_subject)

    @property
    def pubsub_notifications_enabled(self) -> bool:
        return all(
            (
                self.gcp_project_id,
                self.pubsub_notification_topic,
                self.pubsub_push_service_account,
                self.pubsub_push_audience,
            )
        )

    @property
    def session_cookie_name(self) -> str:
        if self.app_env == "production":
            return "__Host-plant_guardian_session"
        return "plant_guardian_session"

    @property
    def session_cookie_secure(self) -> bool:
        return self.app_env == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()
