from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from uuid import UUID, uuid4

from sqlalchemy import Boolean, DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class UserRole(StrEnum):
    """Роли пользователей в системе.

    Бизнес-логика ролей:
    - EMPLOYEE: рядовой сотрудник, работает только со своими данными.
    - MANAGER: руководитель, видит данные своей команды в режиме чтения.
    - DEVELOPER: технический администратор платформы, имеет доступ к developer dashboard.
    """

    EMPLOYEE = "employee"
    MANAGER = "manager"
    DEVELOPER = "developer"


class User(Base):
    """Пользователь системы с учётными данными и ролью доступа."""

    __tablename__ = "users"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    username: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    full_name: Mapped[str] = mapped_column(String(128))
    password_hash: Mapped[str] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Роль определяет, какие разделы системы доступны пользователю.
    # По умолчанию выдаём роль обычного сотрудника: это минимальный набор прав.
    role: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default=UserRole.EMPLOYEE.value,
        server_default=UserRole.EMPLOYEE.value,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    sessions = relationship(
        "UserSession", back_populates="user", cascade="all, delete-orphan"
    )

    # Команды, в которых состоит пользователь.
    teams: Mapped[list] = relationship(
        "Team",
        secondary="user_team_members",
        back_populates="members",
        lazy="selectin",
    )
