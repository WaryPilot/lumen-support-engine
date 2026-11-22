from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

load_dotenv(override=True)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    brand_name: str = "Lumen Audio"
    support_email: str = "lumenaudio.demo@gmail.com"
    poll_interval_seconds: int = 15

    google_client_id: str = ""
    google_client_secret: str = ""
    google_refresh_token: str = ""
    gmail_processed_label: str = "Lumen/Processed"
    gmail_review_label: str = "Lumen/Needs-Review"

    supabase_url: str = ""
    supabase_key: str = ""
    google_api_key: str = ""
    gemini_api_key: str = ""
    triage_model: str = "gemini-2.5-flash-lite"
    resolution_model: str = "gemini-2.5-flash"

    dashboard_username: str = "admin"
    dashboard_password: str = "lumenadmin123"


settings = Settings()
