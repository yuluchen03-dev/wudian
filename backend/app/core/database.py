"""
悟典 - 数据库连接模块
SQLAlchemy 2.0 异步引擎 + 会话管理

支持：
- SQLite（默认，开发环境，使用 aiosqlite）
- PostgreSQL（生产环境，使用 asyncpg）
通过环境变量 DATABASE_URL 切换。
"""
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings


def _build_engine():
    """根据数据库类型构建异步引擎（SQLite 与 PostgreSQL 参数不同）"""
    url = settings.resolved_database_url
    is_sqlite = url.startswith("sqlite")

    if is_sqlite:
        # SQLite 不支持 pool_size / max_overflow / pool_recycle 等参数
        return create_async_engine(
            url,
            echo=settings.APP_DEBUG,
            # SQLite 需要允许在同一线程外使用连接（FastAPI 异步场景）
            connect_args={"check_same_thread": False},
        )

    # PostgreSQL
    return create_async_engine(
        url,
        echo=settings.APP_DEBUG,
        pool_size=10,
        max_overflow=20,
        pool_pre_ping=True,
        pool_recycle=3600,
    )


# 异步引擎
engine = _build_engine()

# 异步会话工厂
async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)


class Base(DeclarativeBase):
    """所有 ORM 模型的声明性基类"""
    pass


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI 依赖注入：获取数据库会话"""
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """初始化数据库（创建所有表）- 仅用于开发环境"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db() -> None:
    """关闭数据库连接"""
    await engine.dispose()
