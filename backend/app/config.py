import os
from functools import lru_cache
from pathlib import Path
from dotenv import load_dotenv
from pydantic import BaseModel, Field

# Locate and load the backend .env file
BACKEND_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = BACKEND_DIR / ".env"
load_dotenv(dotenv_path=ENV_PATH)


class Settings(BaseModel):
    litellm_api_key: str = Field(
        default_factory=lambda: os.getenv("LITELLM_API_KEY", "sk-sT8JcBKlU1yDePay-QyDRA").strip()
    )
    litellm_base_url: str = Field(
        default_factory=lambda: os.getenv(
            "LITELLM_BASE_URL", "https://litellm.vision.aivar.app/v1"
        ).strip()
    )
    litellm_model: str = Field(
        default_factory=lambda: os.getenv("LITELLM_MODEL", "claude-sonnet-4.6").strip()
    )
    neatlogs_api_key: str = Field(
        default_factory=lambda: os.getenv("NEATLOGS_API_KEY", "lsiqslUosXcmLFPbkOiOD2XSQRwTU-Ip").strip()
    )
    crustdata_api_key: str = Field(
        default_factory=lambda: os.getenv("CRUSTDATA_API_KEY", "cd_aae0073e75e8c2f09d4ec562c5e144853430").strip()
    )
    host: str = Field(default_factory=lambda: os.getenv("HOST", "0.0.0.0"))
    port: int = Field(default_factory=lambda: int(os.getenv("PORT", "8000")))
    cors_origins: list[str] = ["*"]


@lru_cache()
def get_settings() -> Settings:
    return Settings()
