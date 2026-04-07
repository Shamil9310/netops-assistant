from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="NETOPS_ASSISTANT_", env_file=".env", extra="ignore")

    app_name: str = "NetOps Assistant API"
    environment: str = "development"
    database_url: str = "postgresql+asyncpg://netops:netops@localhost:5432/netops_assistant"
    secret_key: str = "change-me"
    cors_origins: list[str] = ["http://localhost:3000"]
    session_cookie_name: str = "netops_session"
    session_ttl_hours: int = 12
    bootstrap_username: str = "engineer"
    bootstrap_password: str = "engineer123"
    bootstrap_full_name: str = "Шамиль Исаев"


settings = Settings()
