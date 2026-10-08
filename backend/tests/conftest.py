"""
测试配置文件
设置测试所需的环境变量，确保在导入 app.main 之前完成初始化
"""
import os
import sys
from pathlib import Path

# 添加 backend 目录到 Python 路径
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

# 每次测试会话使用全新的测试数据库（在 app.core.database 导入前删除）
_test_db = backend_dir / "test_wudian.db"
for _suffix in ("", "-wal", "-shm"):
    _p = Path(str(_test_db) + _suffix)
    if _p.exists():
        _p.unlink()

# 设置必需的测试环境变量
# 注意：这些是测试用的占位值，生产环境请务必在 .env 文件中设置强随机密钥
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-for-pytest-only-do-not-use-in-production")
os.environ.setdefault("APP_ENV", "development")
os.environ.setdefault("APP_DEBUG", "false")
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///./test_wudian.db")

# 可选：设置测试用的 AI 配置（如果测试需要）
os.environ.setdefault("OPENAI_API_KEY", "test-key-placeholder")
os.environ.setdefault("AGNES_API_KEY", "test-key-placeholder")


# ============================================================
# 测试夹具
# ============================================================

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture(scope="session")
def base_url():
    """提供测试的基础 URL"""
    return "http://testserver"


@pytest.fixture
def db_session():
    """占位夹具：API 测试通过 TestClient 走应用自身的数据库依赖，无需直接会话"""
    yield None


@pytest.fixture
def client(db_session, base_url):
    """提供 TestClient 用于 API 测试

    注：本环境的 starlette/httpx2 组合下 TestClient 上下文管理器不触发
    lifespan，因此这里显式执行 init_db() 保证测试库表结构存在。
    """
    import asyncio

    from app.core.database import init_db

    asyncio.run(init_db())
    with TestClient(app, base_url=base_url) as test_client:
        yield test_client
    asyncio.run(_dispose_engine())


async def _dispose_engine():
    from app.core.database import engine

    await engine.dispose()
