from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = (
        "postgresql+asyncpg://postgres:postgres@localhost:5432/myperks_development"
    )
    allowed_origins: list[str] = ["http://localhost:3000"]
    openai_api_key: SecretStr = SecretStr("")
    clerk_issuer: str = ""
    clerk_jwks_url: str = ""


settings = Settings()
