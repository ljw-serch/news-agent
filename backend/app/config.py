"""全局配置。

沿用新闻项目原有的环境变量风格（DATABASE_URL / REDIS_* / LLM_*），
同时补齐 JWT、缓存 TTL、上传目录等配置，供 app 分层结构使用。
"""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent  # backend/


class Settings(BaseSettings):
    APP_NAME: str = "AI 新闻资讯平台"
    APP_VERSION: str = "2.0.0"
    DEBUG: bool = True

    # 数据库：保留原有的异步 MySQL 技术栈
    # 必填，只从 .env 读取（如 mysql+asyncmy://user:password@127.0.0.1:3306/dbname?charset=utf8mb4）
    DATABASE_URL: str

    # Redis：保留原有缓存技术栈；Redis 不可用时自动降级，不影响主流程
    REDIS_URL: str = "redis://127.0.0.1:6379/0"
    REDIS_ENABLED: bool = True

    # JWT
    JWT_SECRET_KEY: str = "change-me-in-env"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_HOURS: int = 72

    # 大模型（OpenAI 兼容协议）
    LLM_API_KEY: str = ""
    LLM_BASE_URL: str = "https://api.agnes-ai.cn/v1"
    LLM_MODEL: str = "agnes-2.5-flash"
    LLM_TIMEOUT: int = 90

    # 允许的前端源
    CORS_ORIGINS: str = (
        "http://localhost:5173,http://127.0.0.1:5173,"
        "http://localhost:4173,http://127.0.0.1:4173"
    )

    # 缓存时间（秒）
    CACHE_TTL_CATEGORY: int = 7200
    CACHE_TTL_HOT: int = 300
    CACHE_TTL_STATS: int = 120
    CACHE_TTL_DIGEST: int = 600

    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    @property
    def cors_origins(self) -> list[str]:
        return [item.strip() for item in self.CORS_ORIGINS.split(",") if item.strip()]


settings = Settings()

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
UPLOAD_DIR = BASE_DIR / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".gif",
    ".webp",
    ".svg",
}

# 新闻列表分页限制
MAX_PAGE_SIZE = 100
