from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    db_path: Path = Field(default=Path("./data/storymemory.sqlite3"), alias="STORYMEMORY_DB_PATH")
    data_dir: Path = Field(default=Path("./data"), alias="STORYMEMORY_DATA_DIR")
    export_dir: Path = Field(default=Path("./exports"), alias="STORYMEMORY_EXPORT_DIR")
    llm_provider: str = Field(default="ollama", alias="DEFAULT_MODEL_PROVIDER")
    deepseek_api_key: str | None = Field(default=None, alias="DEEPSEEK_API_KEY")
    deepseek_base_url: str = Field(default="https://api.deepseek.com", alias="DEEPSEEK_BASE_URL")
    deepseek_model: str = Field(default="deepseek-v4-flash", alias="DEEPSEEK_MODEL")
    openai_api_key: str | None = Field(default=None, alias="OPENAI_API_KEY")
    openai_base_url: str = Field(default="https://api.openai.com/v1", alias="OPENAI_BASE_URL")
    openai_model: str = Field(default="gpt-4o-mini", alias="OPENAI_MODEL")
    openai_compatible_api_key: str | None = Field(default=None, alias="OPENAI_COMPATIBLE_API_KEY")
    openai_compatible_base_url: str = Field(default="https://api.openai.com/v1", alias="OPENAI_COMPATIBLE_BASE_URL")
    openai_compatible_model: str = Field(default="gpt-4o-mini", alias="OPENAI_COMPATIBLE_MODEL")
    ollama_base_url: str = Field(default="http://127.0.0.1:11434", alias="OLLAMA_BASE_URL")
    ollama_model: str = Field(default="auto", alias="DEFAULT_OLLAMA_MODEL")

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()


def resolve_path(path: str | Path) -> Path:
    return Path(path).expanduser().resolve()
