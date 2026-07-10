"""
悟典 - 模型基类与公共 Mixin
提供所有表共享的时间戳、软删除等字段

注意：Base (DeclarativeBase) 定义在 app.core.database 中，
此处重新导出以便 app.models.base 仍可作为统一导入入口。
"""
from datetime import datetime
from sqlalchemy import DateTime, Boolean, func, Integer
from sqlalchemy.orm import Mapped, mapped_column

# 重新导出 Base，保持 from app.models.base import Base 可用
from app.core.database import Base  # noqa: F401


class TimestampMixin:
    """时间戳 Mixin：自动管理 created_at 和 updated_at"""
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="创建时间",
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        comment="更新时间",
    )


class SoftDeleteMixin:
    """软删除 Mixin：通过 is_deleted 标记删除"""
    is_deleted: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        index=True,
        comment="是否软删除",
    )


class BaseModelMixin(TimestampMixin, SoftDeleteMixin):
    """基础模型 Mixin：时间戳 + 软删除"""
    pass
