from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    amqp_url: str = "amqp://guest:guest@localhost:5672/"
    postgres_url: str = "postgresql://autoservice:autoservice@localhost:5432/diagnostics"
    exchange: str = "autoservice"
    warehouse_url: str = "http://localhost:8006"

    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()
