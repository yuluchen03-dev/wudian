"""
悟典 - 依赖注入模块
数据库会话、当前用户解析等 FastAPI 依赖
"""
import logging
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.core.security import decode_token
from app.models.user import User

logger = logging.getLogger(__name__)

# OAuth2 password bearer - 用于从 Authorization header 提取 token
# tokenUrl 指向登录端点（用于 Swagger UI 的 "Authorize" 按钮）
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

# 可选认证用：不传 token 也不报错，token 无效时返回 None
oauth2_scheme_optional = OAuth2PasswordBearer(
    tokenUrl="/api/auth/login",
    auto_error=False,
)


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    从 JWT token 解析当前登录用户

    :raises HTTPException 401: token 无效或用户不存在
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无法验证凭据",
        headers={"WWW-Authenticate": "Bearer"},
    )

    payload = decode_token(token)
    if payload is None:
        raise credentials_exception

    # 检查 token 类型
    if payload.get("type") != "access":
        raise credentials_exception

    user_id: Optional[int] = payload.get("sub")
    if user_id is None:
        raise credentials_exception

    # sub 字段存储的是字符串形式的 user_id
    try:
        user_id_int = int(user_id)
    except (ValueError, TypeError):
        raise credentials_exception

    # 从数据库查询用户
    result = await db.execute(select(User).where(User.id == user_id_int))
    user = result.scalar_one_or_none()

    if user is None:
        raise credentials_exception

    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    确保当前用户是激活状态

    :raises HTTPException 403: 用户已被禁用
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="用户已被禁用",
        )
    return current_user


async def get_optional_current_user(
    token: Optional[str] = Depends(oauth2_scheme_optional),
    db: AsyncSession = Depends(get_db),
) -> Optional[User]:
    """
    可选认证：若请求未携带 token 或 token 无效，返回 None；
    若 token 有效，返回对应 User。
    用于"匿名也能访问，登录有额外功能"的接口。
    """
    if token is None:
        return None

    payload = decode_token(token)
    if payload is None:
        return None

    # 只接受 access token
    if payload.get("type") != "access":
        return None

    user_id = payload.get("sub")
    if user_id is None:
        return None

    try:
        user_id_int = int(user_id)
    except (ValueError, TypeError):
        return None

    result = await db.execute(select(User).where(User.id == user_id_int))
    user = result.scalar_one_or_none()

    if user is None or not user.is_active:
        return None

    return user


def _make_demo_user():
    """
    构造一个内存中的 demo 用户对象（不写入数据库，不实例化 SQLAlchemy 模型）。
    用于 development 模式下未登录用户也能调用 AI 接口的 demo 场景。
    返回一个轻量对象，具备 AI 路由所需属性（id/username 等），鸭子类型兼容 User。
    """
    import types
    from datetime import datetime, timezone

    return types.SimpleNamespace(
        id=0,
        username="demo",
        email="demo@wudian.local",
        hashed_password="",
        is_active=True,
        is_superuser=False,
        avatar=None,
        nickname="体验用户",
        bio=None,
        level=1,
        exp_points=0,
        streak_days=0,
        total_study_days=0,
        total_verses_learned=0,
        pk_rating=1000,
        last_login_at=datetime.now(timezone.utc),
        last_study_at=None,
    )


async def get_current_user_or_demo(
    token: Optional[str] = Depends(oauth2_scheme_optional),
    db: AsyncSession = Depends(get_db),
):
    """
    Demo 友好认证：
    - 若请求携带有效 token，返回对应登录用户；
    - 若未携带 token 或 token 无效：
        - development 模式下返回一个 demo 用户（id=0），允许匿名访问；
        - 非 development 模式抛 401。
    用于 AI 接口（如 /api/ai/chat-sage）让 demo 现场无需登录即可体验。
    """
    if token is not None:
        payload = decode_token(token)
        if payload is not None and payload.get("type") == "access":
            user_id = payload.get("sub")
            try:
                user_id_int = int(user_id) if user_id is not None else None
            except (ValueError, TypeError):
                user_id_int = None
            if user_id_int is not None:
                result = await db.execute(
                    select(User).where(User.id == user_id_int)
                )
                user = result.scalar_one_or_none()
                if user is not None and user.is_active:
                    return user

    # token 缺失或无效
    if settings.is_development:
        logger.info("development 模式：未登录用户使用 demo 身份访问 AI 接口")
        return _make_demo_user()

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无法验证凭据",
        headers={"WWW-Authenticate": "Bearer"},
    )
