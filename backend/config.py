from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    groq_api_key: str = ""
    groq_model: str = "llama-3.1-8b-instant"

    embedding_model: str = "intfloat/multilingual-e5-base"

    chroma_db_path: str = "./chroma_db"
    sources_json_path: str = "./data/sources.json"

    top_k_retrieval: int = 5

    backend_port: int = 8000
    cors_origins: str = "http://localhost:5173"

    # Comma-separated path prefixes allowed for PDF serving (security)
    pdf_serve_allowed_paths: str = "C:/Users/,C:/xerg's/"

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",")]

    @property
    def pdf_allowed_prefixes(self) -> list[str]:
        return [p.strip() for p in self.pdf_serve_allowed_paths.split(",")]


@lru_cache
def get_settings() -> Settings:
    return Settings()
