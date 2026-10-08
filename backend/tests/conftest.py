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

# 本进程唯一标识：用于把「测试数据库」与「隔离向量索引」都做成 per-process，
# 彻底消除并发 pytest 之间的相互干扰（见下方两处说明）。
_PID = os.getpid()

# 每次测试会话使用全新的测试数据库（在 app.core.database 导入前删除）。
#
# 为什么必须 per-process：本文件在会话开始就删除并重建该 SQLite 文件；若多个
# pytest 进程共享同一个文件名，后启动者会清掉先启动者的表，产生随机**伪失败**
# （2026-10-08 实测：并发运行 test_auth 出现 4 个伪失败，409 与 KeyError）。
# 用 PID 后缀后每个进程有独立 DB，互不干扰。
_test_db = backend_dir / f"test_wudian_{_PID}.db"
for _suffix in ("", "-wal", "-shm"):
    _p = Path(str(_test_db) + _suffix)
    if _p.exists():
        _p.unlink()

# 设置必需的测试环境变量
# 注意：这些是测试用的占位值，生产环境请务必在 .env 文件中设置强随机密钥
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-for-pytest-only-do-not-use-in-production")
os.environ.setdefault("APP_ENV", "development")
os.environ.setdefault("APP_DEBUG", "false")
os.environ.setdefault("DATABASE_URL", f"sqlite+aiosqlite:///./test_wudian_{_PID}.db")

# ---------------------------------------------------------------------------
# 向量索引隔离（安全硬约束）
# ---------------------------------------------------------------------------
# 本文件第 40 行 `from app.main import app` 会触发 app.main 的启动逻辑，
# 其中包含 rag.build_index()；而 tests/test_debate_classic_rag.py:20/51 更是
# 直接调用 `build_index(force=True)` → rag_service._clear_collection()
# （rag_service.py:638-639 → :607-617），会**清空并重建** collection。
#
# 若不隔离，`pytest tests` 会直接操作真实 backend/chroma_db：
#   - 2026-10-08 曾发生两个并发未隔离 pytest 同时重建真实索引，
#     导致 HNSW 段文件被写入不可读状态（data_level0.bin 167600 → 958672）。
#
# 因此这里强制把 CHROMA_PERSIST_DIR 默认指向**相对**隔离目录：
#   - 必须是相对路径：绝对路径会让 test_hackathon_readiness.py:15-24 的
#     `startswith(backend_root)` 断言失败（config.py 会把它解析到 backend 之下）。
#   - 用 setdefault：调用方仍可显式指定别的隔离目录。
#   - **必须 per-process（PID 后缀）**：早期版本用固定的
#     "./_regression_iso_chroma"，结果两个并发 pytest 会共享同一隔离目录，
#     互相 build_index(force=True) 清空对方，产生**并发索引竞态**
#     （2026-10-08 实测：多成员同时跑测试时出现莫名失败，且互相误判为代码缺陷）。
#     加 PID 后缀后，每个进程写入自己的目录，并发也互不干扰。
# 这样任何人不带隔离变量直接跑 `pytest tests` 也是安全且并发安全的。
# ---------------------------------------------------------------------------
os.environ.setdefault("CHROMA_PERSIST_DIR", f"./_test_iso_chroma_{_PID}")

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
