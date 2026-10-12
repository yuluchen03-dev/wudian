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

# ---------------------------------------------------------------------------
# 测试数据库隔离（安全硬约束，DSH-SA-003 / SA001-02）
# ---------------------------------------------------------------------------
# 原实现用的是「环境里已有则沿用」的写入方式（setdefault）：
#     os.environ.setdefault("DATABASE_URL", ...隔离测试库...)
# 其语义是只要 DATABASE_URL 已经存在（开发者 shell、CI 变量、.env、或继承自
# 父进程），pytest 就**静默采纳**它。若它指向真实数据库，conftest.py 的
# `await init_db()` 会对其 Base.metadata.create_all，TestClient 随后还会写入
# ——测试直接改真实库。
#
# 这与本文件下方 CHROMA_PERSIST_DIR 的 SAFETY-001 修复是**同一类**继承型缺陷：
# 2026-10-08 的索引损坏事故正是「继承来的值指向生产目录」造成的，当时把
# CHROMA_PERSIST_DIR 从 setdefault 改成硬赋值，却漏掉了 DATABASE_URL。
# 本段即补齐这一对称性（两个变量必须同纪律，见 test_conftest_db_isolation.py）。
#
# 现在改为与 CHROMA_PERSIST_DIR 完全相同的两条规则：
#   1) 一律强制指向 per-process 隔离测试库（PID 后缀，见上方 :20-23 的并发竞态说明）；
#   2) 若发现继承来的值**不是**隔离测试库，额外打印醒目警告，让人看见发生了什么。
# 之所以保留相对路径 "./test_wudian_{_PID}.db"：config._resolve_backend_path 会把
# 相对值解析到 backend/ 之下，与上面 :24 删除、:126 init_db() 用的是同一个文件，
# 换成绝对路径会让 test_hackathon_readiness.py 的 startswith(backend_root) 断言失败。
# ---------------------------------------------------------------------------
_ISOLATED_DB_URL = f"sqlite+aiosqlite:///./test_wudian_{_PID}.db"

_inherited_db_url = os.environ.get("DATABASE_URL")
if _inherited_db_url and _inherited_db_url != _ISOLATED_DB_URL:
    print(
        "\n[SAFETY-001/DB] 检测到继承的 DATABASE_URL："
        f"{_inherited_db_url}\n"
        f"    已强制改用本进程隔离测试库 {_ISOLATED_DB_URL}，"
        "以免测试对真实数据库建表/写入。\n",
        file=sys.stderr,
    )
os.environ["DATABASE_URL"] = _ISOLATED_DB_URL

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
# 因此这里强制把 CHROMA_PERSIST_DIR 指向**相对**隔离目录：
#   - 必须是相对路径：绝对路径会让 test_hackathon_readiness.py:15-24 的
#     `startswith(backend_root)` 断言失败（config.py 会把它解析到 backend 之下）。
#   - **必须 per-process（PID 后缀）**：早期版本用固定的
#     "./_regression_iso_chroma"，结果两个并发 pytest 会共享同一隔离目录，
#     互相 build_index(force=True) 清空对方，产生**并发索引竞态**
#     （2026-10-08 实测：多成员同时跑测试时出现莫名失败，且互相误判为代码缺陷）。
#     加 PID 后缀后，每个进程写入自己的目录，并发也互不干扰。
#
# SAFETY-001：**不再使用 setdefault**。
# 原实现用 setdefault，意味着只要环境里已经有 CHROMA_PERSIST_DIR
# （开发者 shell、CI 变量、.env 等），测试就会**沿用**它——如果它指向
# 生产目录 backend/chroma_db，测试将直接操作生产索引，且没有任何提示。
# 这是真实的安全漏洞，2026-10-08 的索引损坏事故即由此类未隔离运行导致。
# 现在改为：
#   1) 一律强制指向 per-process 隔离目录；
#   2) 若发现继承来的值解析后**等于生产目录**，额外打印醒目警告。
# 安全的隔离目录不会被拒绝；只有「指向生产」才会被强制纠正。
# ---------------------------------------------------------------------------
_ISOLATED_CHROMA = f"./_test_iso_chroma_{_PID}"
_PROD_CHROMA_DIR = (backend_dir / "chroma_db").resolve()


def _resolved_from_env(value: str) -> Path:
    """按 config._resolve_backend_path 的同一规则解析（相对路径基于 backend）。"""
    p = Path(value)
    return (p if p.is_absolute() else (backend_dir / p)).resolve()


_inherited = os.environ.get("CHROMA_PERSIST_DIR")
if _inherited and _resolved_from_env(_inherited) == _PROD_CHROMA_DIR:
    print(
        "\n[SAFETY-001] 检测到 CHROMA_PERSIST_DIR 指向**生产索引**"
        f"（{_PROD_CHROMA_DIR}）。已强制改用隔离目录 {_ISOLATED_CHROMA}，"
        "以免测试清空/重建生产索引。\n",
        file=sys.stderr,
    )
os.environ["CHROMA_PERSIST_DIR"] = _ISOLATED_CHROMA

# 可选：设置测试用的 AI 配置（如果测试需要）
os.environ.setdefault("OPENAI_API_KEY", "test-key-placeholder")
os.environ.setdefault("AGNES_API_KEY", "test-key-placeholder")


# ============================================================
# 测试夹具
# ============================================================

import pytest
from fastapi.testclient import TestClient

from app.main import app


# ---------------------------------------------------------------------------
# TEST-HARNESS-INDEX-EMPTY-001 修复：显式构建隔离索引
# ---------------------------------------------------------------------------
# 缺陷：`build_index()` 只注册在 FastAPI 的 lifespan 里（app/main.py:58-74），
# 而本文件的 TestClient 说明（见下方 client 夹具）已明确记录本环境的
# starlette/httpx 组合下 **TestClient 上下文管理器不触发 lifespan**。因此
# 直接调用检索服务的测试（不经 client 夹具的那些）面对的是一个
# collection.count() == 0 的空索引，命中数类断言测的是"没有索引"而不是行为。
#
# 实测证据（隔离副本）：
#   A 生产副本          -> 17 条 sc 查询 0 dead
#   B 空目录            -> 8 dead
#   C 隔离目录+显式建索引 -> 0 dead
#   D 仅 import app.main -> count=0, 8 dead
#   E D + build_index()  -> 0 dead
# 空索引复现出与 RM-005 代码无关的同一组 8 dead，证明是 harness 缺陷。
#
# 修法：加一个 session 级 autouse 夹具，在**隔离目录**上构建一次索引。
# 安全性：CHROMA_PERSIST_DIR 已在本文件上方被硬赋值为 per-PID 隔离目录
# （SAFETY-001），因此 build_index() 只会写测试目录；生产索引不会被打开。
# 另加一道断言，确保隔离目录确实不是生产目录，避免将来有人改动上面的赋值
# 时这里静默变成"重建生产索引"。
# ---------------------------------------------------------------------------
def _assert_isolated_chroma() -> None:
    """硬保证 build_index() 不会作用于生产索引。"""

    def _resolve(value: str) -> Path:
        p = Path(value)
        return (p if p.is_absolute() else (backend_dir / p)).resolve()

    active = _resolve(os.environ["CHROMA_PERSIST_DIR"])
    if active == _PROD_CHROMA_DIR:
        raise RuntimeError(
            "拒绝在**生产索引**上构建测试索引：CHROMA_PERSIST_DIR "
            f"指向 {_PROD_CHROMA_DIR}。这是 SAFETY-001 保护的目录。"
        )
    if active.name.startswith("_test_iso_chroma_") is False:
        raise RuntimeError(
            f"测试索引目录不是预期的 per-PID 隔离目录：{active}"
        )


@pytest.fixture(scope="session", autouse=True)
def _ensure_test_index():
    """在隔离目录上构建一次索引，使检索类断言面对真实语料而非空集合。

    TEST-HARNESS-INDEX-EMPTY-001。不触碰生产索引（上方断言强制）。
    """
    _assert_isolated_chroma()

    from app.services.rag_service import get_rag_service

    rag = get_rag_service()
    if rag.collection is None or rag.collection.count() == 0:
        rag.build_index()
    yield


# ---------------------------------------------------------------------------
# TEST-HARNESS-FORCE-REBUILD-003：进程内只允许一次破坏性重建
# ---------------------------------------------------------------------------
# 缺陷：多个测试类各自调用 ``build_index(force=True)``，而 force 会先
# ``_clear_collection()`` 再重新 upsert。在**同一进程内反复**清空并重建 HNSW
# 段，会在 chromadb 内部留下不一致状态，实测报错：
#
#     chromadb.errors.InternalError:
#         Error in compaction: Failed to apply logs to the hnsw segment writer
#
# 该错误随后使 test_fix003_recall.py 的 7 个用例在 setUpClass 阶段 ERROR。
#
# 实测（21 个模块固定顺序，同一台机器）：
#   原始 conftest                         -> 6 failed, 7 errors
#   + 本文件 _ensure_test_index 夹具      -> 1 failed, 7 errors
# 也就是说这 7 个 ERROR 是**既有缺陷**，与本轮 RM-005/RM-006 改动无关；
# 但它妨碍把测试套件当作可信证据引用，因此在这里一并消除。
#
# 修法：提供共享助手，保证**每进程只做一次**破坏性重建。后续调用若发现索引
# 已就绪且含百家论道语料，就直接复用而不再清空——保留测试原意（在真实索引上
# 断言），同时消除自我破坏的重复重建。
# ---------------------------------------------------------------------------
_REBUILD_DONE = False


def ensure_index_built(rag) -> int:
    """幂等地保证隔离索引已构建。每进程最多一次破坏性重建。

    返回当前 collection 条数。不触碰生产索引（见 _assert_isolated_chroma）。
    """
    global _REBUILD_DONE

    _assert_isolated_chroma()

    if rag.collection is None:
        return 0

    ready = (rag.collection.count() > 0 and rag._collection_has_debate_classics())

    if _REBUILD_DONE and ready:
        return rag.collection.count()

    if not ready:
        rag.build_index(force=True)
    _REBUILD_DONE = True
    return rag.collection.count()



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
