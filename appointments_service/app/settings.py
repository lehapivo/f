from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    amqp_url: str = "amqp://guest:guest@localhost:5672/"
    postgres_url: str = "postgresql://autoservice:autoservice@localhost:5432/appointments"
    exchange: str = "autoservice"
    clients_url: str = "http://localhost:8001"

    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()
