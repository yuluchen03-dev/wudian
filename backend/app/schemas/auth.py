"""
悟典 - 认证相关 Pydantic 数据模型
注册、登录、用户信息、Token 响应
"""
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field


# ============================================================
# 请求模型
# ============================================================

class UserCreate(BaseModel):
    """用户注册请求"""
    username: str = Field(
        ..., min_length=2, max_length=50,
        description="用户名（2-50 字符）",
    )
    email: EmailStr = Field(..., description="邮箱地址")
    password: str = Field(
        ..., min_length=6, max_length=128,
        description="密码（6-128 字符）",
    )


class UserLogin(BaseModel):
    """用户登录请求"""
    username: str = Field(..., description="用户名或邮箱")
    password: str = Field(..., description="密码")


class RefreshTokenRequest(BaseModel):
    """刷新 token 请求"""
    refresh_token: str = Field(..., description="refresh token")


# ============================================================
# 响应模型
# ============================================================

class UserResponse(BaseModel):
    """用户信息响应"""
    id: int = Field(..., description="用户 ID")
    username: str = Field(..., description="用户名")
    email: str = Field(..., description="邮箱")
    nickname: Optional[str] = Field(None, description="昵称")
    avatar: Optional[str] = Field(None, description="头像 URL")
    bio: Optional[str] = Field(None, description="个人简介")
    level: int = Field(1, description="用户等级")
    exp_points: int = Field(0, description="经验值")
    streak_days: int = Field(0, description="连续学习天数")
    total_study_days: int = Field(0, description="总学习天数")
    total_verses_learned: int = Field(0, description="已学经文数")

    model_config = ConfigDict(from_attributes=True)


class Token(BaseModel):
    """Token 响应"""
    access_token: str = Field(..., description="JWT access token")
    refresh_token: str = Field(..., description="JWT refresh token")
    token_type: str = Field("bearer", description="token 类型")
    user: UserResponse = Field(..., description="用户信息")


class TokenData(BaseModel):
    """Token 解析后的数据"""
    user_id: Optional[int] = Field(None, description="用户 ID")
    username: Optional[str] = Field(None, description="用户名")
