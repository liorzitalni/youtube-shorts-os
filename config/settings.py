"""
Central configuration. All settings flow from .env via pydantic-settings.
Access anywhere: from config.settings import settings
"""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # --- AI ---
    anthropic_api_key: str = Field(..., alias="ANTHROPIC_API_KEY")
    claude_model_smart: str = "claude-sonnet-4-6"    # Scripting, analysis
    claude_model_fast: str = "claude-haiku-4-5-20251001"     # Bulk idea gen, metadata

    # --- TTS ---
    elevenlabs_api_key: str = Field(..., alias="ELEVENLABS_API_KEY")
    elevenlabs_voice_id: str = Field(..., alias="ELEVENLABS_VOICE_ID")

    # --- YouTube ---
    youtube_client_secrets_path: str = "config/client_secrets.json"
    youtube_token_path: str = "config/youtube_token.json"
    youtube_channel_id: str = Field(..., alias="YOUTUBE_CHANNEL_ID")

    # --- TikTok ---
    tiktok_client_key: str = Field("", alias="TIKTOK_CLIENT_KEY")
    tiktok_client_secret: str = Field("", alias="TIKTOK_CLIENT_SECRET")
    tiktok_token_path: str = "config/tiktok_token.json"

    # --- Instagram ---
    instagram_access_token: str = Field("", alias="INSTAGRAM_ACCESS_TOKEN")
    instagram_account_id: str = Field("", alias="INSTAGRAM_ACCOUNT_ID")

    # --- Stock Footage ---
    pexels_api_key: str = Field("", alias="PEXELS_API_KEY")
    pixabay_api_key: str = Field("", alias="PIXABAY_API_KEY")

    # --- Database ---
    database_path: str = "data/shorts_os.db"

    # --- Paths ---
    output_dir: str = "output"
    assets_dir: str = "data/assets"
    templates_dir: str = "modules/render/templates"

    # --- Pipeline ---
    publish_mode: str = "manual"           # manual | auto
    daily_video_target: int = 2
    idea_backlog_min: int = 14
    human_review_scripts: bool = True
    human_review_videos: bool = True

    # --- Scheduling (cron expressions) ---
    research_cron: str = "0 6 * * 1"
    production_cron: str = "0 7 * * *"
    publish_cron: str = "0 9,17 * * *"
    analytics_cron: str = "0 8 * * *"

    # --- Logging ---
    log_level: str = "INFO"
    log_file: str = "logs/pipeline.log"


settings = Settings()
