"""
悟典 - 安全工具模块
密码哈希（bcrypt）与 JWT token 生成/验证
"""
from datetime import datetime, timedelta, timezone
from typing import Optional

import bcrypt
from jose import JWTError, jwt

from app.core.config import settings


# ============================================================
# 密码哈希（直接使用 bcrypt 库，兼容 Python 3.14）
# ============================================================

def get_password_hash(password: str) -> str:
    """对明文密码进行 bcrypt 哈希"""
    # bcrypt 限制 72 字节，截断处理
    pwd_bytes = password.encode("utf-8")[:72]
    return bcrypt.hashpw(pwd_bytes, bcrypt.gensalt()).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证明文密码与哈希密码是否匹配"""
    try:
        pwd_bytes = plain_password.encode("utf-8")[:72]
        hashed_bytes = hashed_password.encode("utf-8")
        return bcrypt.checkpw(pwd_bytes, hashed_bytes)
    except (ValueError, TypeError):
        return False


# ============================================================
# JWT Token
# ============================================================

def create_access_token(
    data: dict,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """
    生成 JWT access token

    :param data: 要编码进 token 的数据（至少包含 "sub" 字段）
    :param expires_delta: 过期时间增量，不传则使用默认配置
    :return: 编码后的 JWT 字符串
    """
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta
        or timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire, "type": "access"})
    return jwt.encode(
        to_encode,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )


def create_refresh_token(data: dict) -> str:
    """
    生成 JWT refresh token（有效期更长，仅用于刷新 access token）

    :param data: 要编码进 token 的数据（至少包含 "sub" 字段）
    :return: 编码后的 JWT 字符串
    """
    to_encode = data.copy()
    # refresh token 有效期为 access token 的 7 倍
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 7
    )
    to_encode.update({"exp": expire, "type": "refresh"})
    return jwt.encode(
        to_encode,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )


def decode_token(token: str) -> Optional[dict]:
    """
    解码并验证 JWT token

    :param token: JWT 字符串
    :return: 解码后的 payload 字典，验证失败返回 None
    """
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
        return payload
    except JWTError:
        return None
