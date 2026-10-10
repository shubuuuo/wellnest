from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# services/api/app/core/config.py -> repo root is 4 levels up
ROOT_DIR = Path(__file__).resolve().parents[4]
API_PREFIX = "/api/v1"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=ROOT_DIR / ".env", env_ignore_empty=True, extra="ignore")

    app_name: str = "WellNest Tiny API"
    cors_origins: str = "http://localhost:3000"  # comma-separated

    ollama_url: str = "http://localhost:11434"
    chat_model: str = "qwen2.5:3b"
    embed_model: str = "bge-m3"

    database_url: str = ""
    test_database_url: str = ""

    jwt_secret: str = ""
    jwt_expire_minutes: int = 480
    cookie_name: str = "wn_session"
    cookie_secure: bool = False

    admin_email: str = ""
    admin_password: str = ""
    admin_name: str = "Shubham"

    # model_store_path: Path = Path("model_store")
    # online_learning_enabled: bool = True
    # online_batch_size: int = 1
    # online_learning_rate: float = 0.01
    # auto_promote_guard_tolerance: float = 0.02
    # demo_mode: bool = True

    model_store_path: Path = ROOT_DIR / "model_store"   
    online_learning_enabled: bool = True
    online_batch_size: int = 1
    online_learning_rate: float = 0.01
    auto_promote_guard_tolerance: float = 0.02
    demo_mode: bool = True

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()