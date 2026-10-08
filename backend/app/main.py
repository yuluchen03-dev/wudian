"""
悟典 - 四书五经互动学习平台
FastAPI 应用入口
"""
import sys
from contextlib import asynccontextmanager

# Windows 控制台 UTF-8 支持（避免 emoji/中文输出报错）
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.database import init_db, close_db


def _validate_config() -> None:
    """校验关键配置项，缺失或异常时打印警告但不中断启动"""
    if not settings.JWT_SECRET_KEY:
        print("⚠️ JWT_SECRET_KEY 未设置，认证功能将不可用")

    if settings.is_sqlite:
        db_path = settings.resolved_database_path
        if not db_path:
            print("⚠️ 数据库路径解析失败，使用默认路径")
        else:
            from pathlib import Path
            db_file = Path(db_path)
            if not db_file.parent.exists():
                db_file.parent.mkdir(parents=True, exist_ok=True)
                print(f"📁 创建数据库目录: {db_file.parent}")

    chroma_dir = Path(settings.resolved_chroma_persist_dir)
    if not chroma_dir.exists():
        chroma_dir.mkdir(parents=True, exist_ok=True)
        print(f"📁 创建 ChromaDB 目录: {chroma_dir}")

    debate_dir = Path(settings.resolved_debate_storage_dir)
    if not debate_dir.exists():
        debate_dir.mkdir(parents=True, exist_ok=True)
        print(f"📁 创建辩论数据目录: {debate_dir}")

    try:
        llm_cfg = settings.llm_config
        if not llm_cfg.get("api_key"):
            print("⚠️ LLM API_KEY 未配置，AI 接口将返回降级回复")
    except Exception:
        print("⚠️ LLM 配置校验失败")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动
    print(f"🚀 {settings.APP_NAME} 启动中...")

    # 配置校验
    _validate_config()

    if settings.is_development:
        await init_db()
        print("📦 数据库表已初始化")

    # RAG 索引初始化（启动时检查，不存在则构建）
    try:
        from app.services.rag_service import get_rag_service
        rag = get_rag_service()
        count = rag.build_index()
        if rag.is_available:
            print(f"📚 RAG 索引就绪（{count} 条经文）")
        else:
            print("⚠️ RAG 索引不可用（chromadb 未安装且文件索引为空）")
    except Exception as e:
        print(f"⚠️ RAG 索引初始化失败（不阻断启动）: {e}")

    # LLM 客户端状态检查
    try:
        from app.services.llm_client import llm_client
        if llm_client.is_available:
            print(f"🤖 LLM 客户端就绪（provider={settings.LLM_PROVIDER}, model={llm_client.model}）")
        else:
            print("⚠️ LLM 客户端未就绪（openai 未安装或 API_KEY 未配置），AI 接口将返回降级回复")
    except Exception as e:
        print(f"⚠️ LLM 客户端检查失败（不阻断启动）: {e}")

    print(f"✅ {settings.APP_NAME} 已启动 - {settings.APP_HOST}:{settings.APP_PORT}")
    yield
    # 关闭
    await close_db()
    print(f"👋 {settings.APP_NAME} 已关闭")


# 创建 FastAPI 应用
app = FastAPI(
    title=settings.APP_NAME,
    description="四书五经互动学习平台 API",
    version="0.1.0",
    docs_url="/docs" if settings.is_development else None,
    redoc_url="/redoc" if settings.is_development else None,
    lifespan=lifespan,
)

# CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ===== 健康检查 =====

@app.get("/", tags=["健康检查"])
async def root():
    """根路径"""
    return {
        "app": settings.APP_NAME,
        "version": "0.1.0",
        "status": "running",
        "docs": "/docs" if settings.is_development else "disabled",
    }


@app.get("/health", tags=["健康检查"])
async def health_check():
    """健康检查端点

    返回演示就绪信号（LLM/RAG 状态）与存储位置的相对路径，
    不暴露服务器绝对路径等敏感信息。
    """
    llm_available = False
    llm_model = settings.llm_config.get("model", "unknown")
    try:
        from app.services.llm_client import llm_client
        llm_available = bool(llm_client.is_available)
        llm_model = llm_client.model
    except Exception:
        pass

    rag_available = False
    rag_count = 0
    try:
        from app.services.rag_service import get_rag_service
        rag = get_rag_service()
        rag_available = bool(rag.is_available)
        if getattr(rag, "collection", None) is not None:
            rag_count = rag.collection.count()
        else:
            rag_count = len(getattr(rag, "_file_index", []) or []) + len(
                getattr(rag, "_commentary_index", []) or []
            )
    except Exception:
        pass

    healthy = llm_available and rag_available

    # 脱敏：只返回配置中的相对路径/文件名，不返回服务器绝对路径
    if settings.is_sqlite:
        database_path = settings.DATABASE_URL.rsplit("/", 1)[-1]
    else:
        database_path = "postgresql"

    return {
        "status": "healthy" if healthy else "unhealthy",
        "healthy": healthy,
        "env": settings.APP_ENV,
        "llm_available": llm_available,
        "llm_provider": settings.LLM_PROVIDER,
        "llm_model": llm_model,
        "rag_available": rag_available,
        "rag_count": rag_count,
        "database_path": database_path,
        "chroma_persist_dir": settings.CHROMA_PERSIST_DIR,
        "debate_storage_dir": settings.DEBATE_STORAGE_DIR,
    }


# ===== 路由注册 =====
# 以下路由将在后续迭代中实现并注册
# from app.api import auth, users, classics, progress, srs, quiz, notes, community
# app.include_router(auth.router, prefix="/api/auth", tags=["认证"])
# app.include_router(users.router, prefix="/api/users", tags=["用户"])
# app.include_router(classics.router, prefix="/api/classics", tags=["经典文献"])
# app.include_router(progress.router, prefix="/api/progress", tags=["学习进度"])
# app.include_router(srs.router, prefix="/api/srs", tags=["间隔重复"])
# app.include_router(quiz.router, prefix="/api/quiz", tags=["题库"])
# app.include_router(notes.router, prefix="/api/notes", tags=["笔记"])
# app.include_router(community.router, prefix="/api/community", tags=["社区"])

# AI 智能讲解路由（router 内部已设 prefix="/api/ai"）
from app.api import ai
app.include_router(ai.router)

# 社区共学路由（router 内部已设 prefix="/api/community"）
from app.api import community
app.include_router(community.router)

# 趣味内容路由（router 内部已设 prefix="/api/content"）
from app.api import content
app.include_router(content.router)

# 学习游戏化路由（router 内部已设 prefix="/api/learning"）
from app.api import learning
app.include_router(learning.router)

# 互动探索路由（router 内部已设 prefix="/api/exploration"）
from app.api import exploration
app.include_router(exploration.router)

# 认证路由（router 内部已设 prefix="/api/auth"）
from app.api import auth
app.include_router(auth.router)

# 经典文献路由（router 内部已设 prefix="/api/classics"）
from app.api import classics
app.include_router(classics.router)

# 百家论道辩论路由（router 内部已设 prefix="/api/debate"）
from app.api import debate
app.include_router(debate.router)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.APP_HOST,
        port=settings.APP_PORT,
        reload=settings.is_development,
    )
