from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    wassist_api_key: str = ""
    wassist_base_url: str = "https://api.wassist.app"

    supabase_url: str = ""
    supabase_service_key: str = ""

    deepseek_api_key: str = ""
    deepseek_base_url: str = "https://api.deepseek.com"

    google_api_key: str = ""

    manus_api_key: str = ""
    manus_base_url: str = "https://api.manus.ai"

    paypal_client_id: str = ""
    paypal_client_secret: str = ""
    paypal_plan_id: str = ""
    paypal_base_url: str = "https://api-m.sandbox.paypal.com"

    demo_mode: bool = True
    skip_paywall: bool = False
    mock_delay_portal_url: str = "http://localhost:8000/mock-portal"


settings = Settings()
