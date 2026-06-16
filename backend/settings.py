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

    # AI_BACKEND controls which AI provider is used.
    # Allowed values: "ollama" | "openai"
    #   ollama  — local Ollama models, no API key needed (default)
    #   openai  — OpenAI API (requires OPENAI_API_KEY)
    ai_backend: str = "ollama"
    ollama_base_url: str = "http://localhost:11434"
    ollama_embed_model: str = "nomic-embed-text"
    ollama_chat_model: str = "llama3.2"


settings = Settings()
