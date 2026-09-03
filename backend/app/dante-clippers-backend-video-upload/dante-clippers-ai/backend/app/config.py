from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    env: str = "development"
    secret_key: str = "change-me"

    database_url: str = "postgresql://dante:dante@localhost:5432/dante_clippers"
    redis_url: str = "redis://localhost:6379/0"

    storage_bucket: str = "dante-clippers-dev"
    storage_region: str = "us-east-1"
    aws_access_key_id: str = ""
    aws_secret_access_key: str = ""

    monthly_free_credits: int = 60

    # Used to build full playback URLs for locally-stored files (see
    # services/storage.py). Set this to http://YOUR-PC-LAN-IP:8000 so a
    # phone on the same network can load clips -- "localhost" only means
    # something on the computer running the server itself.
    public_base_url: str = "http://localhost:8000"

    anthropic_api_key: str = ""
    anthropic_model: str = "claude-haiku-4-5-20251001"
    whisper_model_size: str = "base"

    tiktok_client_key: str = ""
    tiktok_client_secret: str = ""
    instagram_app_id: str = ""
    instagram_app_secret: str = ""
    twitch_client_id: str = ""
    twitch_client_secret: str = ""
    youtube_client_id: str = ""
    youtube_client_secret: str = ""

    class Config:
        env_file = ".env"


settings = Settings()
