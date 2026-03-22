from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    GROQ_API_KEY: str = ""
    DATABASE_URL: str
    REDIS_URL: str
    RABBITMQ_URL: str
    META_VERIFY_TOKEN: str
    META_ACCESS_TOKEN: str
    TWILIO_ACCOUNT_SID: str
    TWILIO_AUTH_TOKEN: str
    SENDGRID_API_KEY: str
    TWITTER_BEARER_TOKEN: str
    BANK_ID: str = "union_bank_demo"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
