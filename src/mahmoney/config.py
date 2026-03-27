from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Database
    database_url: str = "postgresql+asyncpg://mahmoney:changeme@db:5432/mahmoney"

    # IMAP
    imap_host: str = ""
    imap_user: str = ""
    imap_password: str = ""
    imap_folder: str = "INBOX"
    poll_interval_seconds: int = 300

    # VLM OCR
    vlm_api_key: str = ""
    vlm_api_url: str = "https://api.fireworks.ai/inference/v1"
    vlm_model: str = "accounts/fireworks/models/qwen2p5-vl-72b-instruct"

    # Storage
    storage_path: Path = Path("/data/receipts")

    # Auth
    auth_password: str = "changeme"  # noqa: S105
    session_secret: str = "change-this-to-a-random-secret-key"  # noqa: S105


def get_settings() -> Settings:
    return Settings()
