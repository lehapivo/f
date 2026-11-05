from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    amqp_url: str = "amqp://guest:guest@localhost:5672/"
    postgres_url: str = "postgresql://autoservice:autoservice@localhost:5432/payments"
    exchange: str = "autoservice"
    billing_url: str = "http://localhost:8007"

    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()
