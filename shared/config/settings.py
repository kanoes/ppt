"""Application configuration loaded from environment variables."""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from typing import Optional

from dotenv import load_dotenv

load_dotenv(override=True)


@dataclass(frozen=True)
class Settings:
    """Strongly-typed view over environment configuration."""

    cors_origins: list[str]
    mode: str
    default_llm_deployment: str
    default_llm_temperature: float
    html_llm_temperature: float
    azure_openai_endpoint: Optional[str]
    azure_openai_api_key: Optional[str]
    postgres_conn_string: Optional[str]
    ppt_shared_directory: Optional[str]
    generated_files_dir: str
    app_id: str
    coreauth_root_url: Optional[str]
    coreauth_app_id: Optional[str]
    coreauth_app_secret: Optional[str]


@lru_cache
def get_settings() -> Settings:
    """Load configuration once and cache it for future calls."""

    import os

    cors_origins_raw = os.getenv("CORS_ORIGINS", "*")
    cors_origins = [origin.strip() for origin in cors_origins_raw.split(",") if origin.strip()]
    if not cors_origins:
        cors_origins = ["*"]

    default_temperature_raw = os.getenv("DEFAULT_LLM_TEMPERATURE", "0.3")
    try:
        llm_temperature = float(default_temperature_raw)
    except ValueError:
        llm_temperature = 0.3

    html_temperature_raw = os.getenv("DEFAULT_HTML_LLM_TEMPERATURE")
    if html_temperature_raw is None:
        html_temperature = 1.0
    else:
        try:
            html_temperature = float(html_temperature_raw)
        except ValueError:
            html_temperature = 1.0

    generated_files_dir = os.getenv("GENERATED_FILES_DIR", "generated_files")

    return Settings(
        cors_origins=cors_origins,
        mode=os.getenv("MODE", "html").lower(),
        default_llm_deployment=os.getenv("DEFAULT_LLM_DEPLOYMENT", "gpt-5"),
        default_llm_temperature=llm_temperature,
        html_llm_temperature=html_temperature,
        azure_openai_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        azure_openai_api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        postgres_conn_string=os.getenv("POSTGRES_CONN_STRING"),
        ppt_shared_directory=os.getenv("PPTAUTO_SHARED_DIRECTORY"),
        generated_files_dir=generated_files_dir,
        app_id=os.getenv("APP_ID", "ppt-automate"),
        coreauth_root_url=os.getenv("COREAUTH_ROOT_URL"),
        coreauth_app_id=os.getenv("COREAUTH_APP_ID"),
        coreauth_app_secret=os.getenv("COREAUTH_APP_SECRET"),
    )


settings = get_settings()
