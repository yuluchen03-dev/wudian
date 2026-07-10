"""
悟典 - 应用核心配置模块
使用 pydantic-settings 进行环境变量管理
"""
from pathlib import Path
from typing import List
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """应用配置类，从环境变量或 .env 文件加载"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # --- 应用配置 ---
    APP_NAME: str = "悟典"
    APP_ENV: str = "development"
    APP_DEBUG: bool = True
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000

    # --- 数据库配置 ---
    # 默认使用 SQLite（MVP 阶段无需安装 PostgreSQL）
    # 生产环境通过环境变量 DATABASE_URL 切换到 PostgreSQL：
    #   DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/db
    POSTGRES_USER: str = "wudian"
    POSTGRES_PASSWORD: str = ""
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: str = "5432"
    POSTGRES_DB: str = "wudian_db"
    DATABASE_URL: str = "sqlite+aiosqlite:///./wudian.db"

    # --- Redis 配置 ---
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: str = ""

    # --- JWT 配置 ---
    JWT_SECRET_KEY: str = "change-me-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440

    # --- OpenAI / AI 配置 ---
    OPENAI_API_KEY: str = ""
    OPENAI_BASE_URL: str = "https://api.openai.com/v1"
    OPENAI_MODEL: str = "gpt-4o-mini"
    EMBEDDING_MODEL: str = "text-embedding-3-small"

    # --- LLM Provider 切换 (openai / deepseek / qwen / local) ---
    LLM_PROVIDER: str = "openai"
    AGNES_API_KEY: str = ""
    AGNES_BASE_URL: str = "https://apihub.agnes-ai.com/v1"
    AGNES_MODEL: str = "agnes-2.0-flash"
    AGNES_IMAGE_MODEL: str = "agnes-image-2.1-flash"
    DEEPSEEK_API_KEY: str = ""
    DEEPSEEK_BASE_URL: str = "https://api.deepseek.com/v1"
    DEEPSEEK_MODEL: str = "deepseek-chat"
    QWEN_API_KEY: str = ""
    QWEN_BASE_URL: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    QWEN_MODEL: str = "qwen-plus"
    LOCAL_LLM_BASE_URL: str = "http://localhost:11434/v1"
    LOCAL_LLM_MODEL: str = "qwen2.5:7b"

    # --- LLM 调用控制 ---
    LLM_TEMPERATURE: float = 0.7
    LLM_MAX_TOKENS: int = 2000
    LLM_TIMEOUT: int = 60
    LLM_MAX_RETRIES: int = 3
    LLM_RETRY_DELAY: float = 1.0

    # --- 成本控制 (每日 token 上限) ---
    DAILY_TOKEN_LIMIT: int = 2_000_000
    TOKEN_COST_WARN_RATIO: float = 0.8

    # --- RAG 配置 ---
    RAG_TOP_K: int = 5
    RAG_SIMILARITY_THRESHOLD: float = 0.65
    RAG_CHUNK_SIZE: int = 300
    RAG_CHUNK_OVERLAP: int = 50
    RAG_EMBEDDING_PROVIDER: str = "local"

    # --- ChromaDB 向量数据库 ---
    CHROMA_PERSIST_DIR: str = "./chroma_db"
    CHROMA_COLLECTION: str = "wudian_verses"

    # --- CORS ---
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3001",
        "http://localhost:5173",
    ]

    # --- 辩论系统配置 ---
    DEBATE_MAX_ROUNDS: int = 3
    DEBATE_DEFAULT_PARTICIPANTS: List[str] = ["confucius", "laozi", "mozi", "hanfeizi"]
    DEBATE_EXTRA_SAGES: List[str] = [
        "mencius",
        "wang_yangming",
        "li_bai",
        "su_shi",
        "fan_zhongyan",
        "wang_anshi",
        "zhuge_liang",
    ]
    DEBATE_STORAGE_DIR: str = "data/debates"

    # --- SRS 间隔重复算法 ---
    SRS_INITIAL_EASE_FACTOR: float = 2.5
    SRS_MINIMUM_EASE_FACTOR: float = 1.3
    SRS_INITIAL_INTERVAL: int = 1
    SRS_EASY_BONUS: float = 1.3

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        """支持 JSON 数组字符串或逗号分隔字符串"""
        if isinstance(v, str):
            import json
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                return [origin.strip() for origin in v.split(",")]
        return v

    @property
    def backend_root(self) -> Path:
        """Backend project root used to resolve demo-local data paths."""
        return Path(__file__).resolve().parents[2]

    def _resolve_backend_path(self, value: str) -> Path:
        path = Path(value)
        if not path.is_absolute():
            path = self.backend_root / value
        return path.resolve()

    @property
    def resolved_database_path(self) -> str:
        """Absolute SQLite database path for health checks and demo startup."""
        if not self.DATABASE_URL.startswith("sqlite"):
            return ""

        if ":///" in self.DATABASE_URL:
            raw_path = self.DATABASE_URL.split(":///", 1)[1]
        else:
            raw_path = self.DATABASE_URL.rsplit("/", 1)[-1]

        return str(self._resolve_backend_path(raw_path))

    @property
    def resolved_database_url(self) -> str:
        """Database URL with SQLite paths pinned to the backend directory."""
        if not self.DATABASE_URL.startswith("sqlite"):
            return self.DATABASE_URL

        if self.DATABASE_URL.startswith("sqlite+aiosqlite"):
            scheme = "sqlite+aiosqlite"
        else:
            scheme = "sqlite"

        return f"{scheme}:///{Path(self.resolved_database_path).as_posix()}"

    @property
    def resolved_chroma_persist_dir(self) -> str:
        return str(self._resolve_backend_path(self.CHROMA_PERSIST_DIR))

    @property
    def resolved_debate_storage_dir(self) -> str:
        return str(self._resolve_backend_path(self.DEBATE_STORAGE_DIR))

    @property
    def llm_config(self) -> dict:
        """根据 LLM_PROVIDER 返回当前 provider 的配置"""
        provider = self.LLM_PROVIDER.lower()
        if provider == "agnes":
            return {
                "api_key": self.AGNES_API_KEY or self.OPENAI_API_KEY,
                "base_url": self.AGNES_BASE_URL,
                "model": self.AGNES_MODEL,
            }
        elif provider == "deepseek":
            return {
                "api_key": self.DEEPSEEK_API_KEY,
                "base_url": self.DEEPSEEK_BASE_URL,
                "model": self.DEEPSEEK_MODEL,
            }
        elif provider == "qwen":
            return {
                "api_key": self.QWEN_API_KEY,
                "base_url": self.QWEN_BASE_URL,
                "model": self.QWEN_MODEL,
            }
        elif provider == "local":
            return {
                "api_key": "not-needed",
                "base_url": self.LOCAL_LLM_BASE_URL,
                "model": self.LOCAL_LLM_MODEL,
            }
        else:  # openai
            return {
                "api_key": self.OPENAI_API_KEY,
                "base_url": self.OPENAI_BASE_URL,
                "model": self.OPENAI_MODEL,
            }

    @property
    def sync_database_url(self) -> str:
        """同步数据库 URL（用于 Alembic 迁移）"""
        url = self.resolved_database_url
        if url.startswith("postgresql+asyncpg"):
            return url.replace("postgresql+asyncpg", "postgresql+psycopg2")
        if url.startswith("sqlite+aiosqlite"):
            return url.replace("sqlite+aiosqlite", "sqlite")
        return url

    @property
    def is_sqlite(self) -> bool:
        """是否使用 SQLite 数据库"""
        return self.DATABASE_URL.startswith("sqlite")

    @property
    def redis_url(self) -> str:
        """Redis 连接 URL"""
        if self.REDIS_PASSWORD:
            return f"redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"

    @property
    def is_development(self) -> bool:
        return self.APP_ENV == "development"

    @property
    def is_production(self) -> bool:
        return self.APP_ENV == "production"


# 全局配置单例
settings = Settings()
