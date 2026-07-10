"""
悟典 - 认证 API 路由

接口：
- POST /api/auth/register   注册
- POST /api/auth/login      登录（返回 access_token + refresh_token）
- GET  /api/auth/me         获取当前用户信息
- POST /api/auth/refresh    刷新 access_token
"""
import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_active_user
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    get_password_hash,
    verify_password,
)
from app.models.user import User
from app.schemas.auth import (
    RefreshTokenRequest,
    Token,
    UserCreate,
    UserLogin,
    UserResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/auth", tags=["认证"])


# ============================================================
# 注册
# ============================================================

@router.post(
    "/register",
    response_model=Token,
    status_code=status.HTTP_201_CREATED,
    summary="用户注册",
)
async def register(
    user_in: UserCreate,
    db: AsyncSession = Depends(get_db),
):
    """
    注册新用户

    - **username**: 用户名（2-50 字符，唯一）
    - **email**: 邮箱（唯一）
    - **password**: 密码（6-128 字符，bcrypt 哈希存储）

    注册成功后直接返回 token，无需再次登录。
    """
    # 检查用户名是否已存在
    existing = await db.execute(
        select(User).where(User.username == user_in.username)
    )
    if existing.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="用户名已被注册",
        )

    # 检查邮箱是否已存在
    existing = await db.execute(
        select(User).where(User.email == user_in.email)
    )
    if existing.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="邮箱已被注册",
        )

    # 创建用户
    user = User(
        username=user_in.username,
        email=user_in.email,
        hashed_password=get_password_hash(user_in.password),
        nickname=user_in.username,
        is_active=True,
    )
    db.add(user)
    await db.flush()  # 获取自增 ID

    # 生成 token
    token_data = {"sub": str(user.id), "username": user.username}
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)

    logger.info("新用户注册: id=%s, username=%s", user.id, user.username)

    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        user=UserResponse.model_validate(user),
    )


# ============================================================
# 登录
# ============================================================

@router.post(
    "/login",
    response_model=Token,
    summary="用户登录",
)
async def login(
    user_in: UserLogin,
    db: AsyncSession = Depends(get_db),
):
    """
    用户登录

    - **username**: 用户名或邮箱
    - **password**: 密码

    登录成功返回 access_token 和 refresh_token。
    """
    # 支持用户名或邮箱登录
    result = await db.execute(
        select(User).where(
            (User.username == user_in.username)
            | (User.email == user_in.username)
        )
    )
    user = result.scalar_one_or_none()

    if user is None or not verify_password(user_in.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="用户已被禁用",
        )

    # 更新最后登录时间
    user.last_login_at = datetime.now(timezone.utc)
    await db.flush()

    # 生成 token
    token_data = {"sub": str(user.id), "username": user.username}
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)

    logger.info("用户登录: id=%s, username=%s", user.id, user.username)

    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        user=UserResponse.model_validate(user),
    )


# ============================================================
# 获取当前用户信息
# ============================================================

@router.get(
    "/me",
    response_model=UserResponse,
    summary="获取当前用户信息",
)
async def get_me(
    current_user: User = Depends(get_current_active_user),
):
    """获取当前登录用户的详细信息（需要登录）"""
    return UserResponse.model_validate(current_user)


# ============================================================
# 刷新 token
# ============================================================

@router.post(
    "/refresh",
    response_model=Token,
    summary="刷新 access token",
)
async def refresh_token(
    body: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    使用 refresh_token 刷新 access_token

    - **refresh_token**: 登录时返回的 refresh_token
    """
    payload = decode_token(body.refresh_token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="refresh_token 无效或已过期",
        )

    # 必须是 refresh 类型
    if payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="token 类型错误，请使用 refresh_token",
        )

    user_id_str = payload.get("sub")
    if user_id_str is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="token 内容无效",
        )

    # 查询用户确认仍然存在且激活
    try:
        user_id = int(user_id_str)
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="token 内容无效",
        )

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户不存在或已被禁用",
        )

    # 生成新的 token 对
    token_data = {"sub": str(user.id), "username": user.username}
    new_access_token = create_access_token(token_data)
    new_refresh_token = create_refresh_token(token_data)

    return Token(
        access_token=new_access_token,
        refresh_token=new_refresh_token,
        token_type="bearer",
        user=UserResponse.model_validate(user),
    )
