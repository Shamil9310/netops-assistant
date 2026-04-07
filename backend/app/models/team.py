from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, String, Table, Column, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

# Таблица связи many-to-many: один пользователь может состоять в нескольких командах,
# одна команда включает нескольких пользователей.
user_team_association = Table(
    "user_team_members",
    Base.metadata,
    Column("user_id", ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    Column("team_id", ForeignKey("teams.id", ondelete="CASCADE"), primary_key=True),
)


class Team(Base):
    """Команда (подразделение) — группа сотрудников под одним руководителем.

    Manager видит данные всех участников своей команды в режиме чтения.
    Один пользователь может быть в нескольких командах.
    """

    __tablename__ = "teams"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(String(512), nullable=True)

    # manager_id — пользователь с ролью MANAGER, отвечающий за эту команду.
    # Может быть None (команда без руководителя — техническое состояние).
    manager_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Участники команды — связь через user_team_association.
    members: Mapped[list] = relationship(
        "User",
        secondary=user_team_association,
        back_populates="teams",
        lazy="selectin",
    )

    manager: Mapped[object | None] = relationship(
        "User",
        foreign_keys=[manager_id],
        lazy="selectin",
    )
