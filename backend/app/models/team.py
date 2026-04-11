from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, String, Table, Column, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

# Таблица связи "многие ко многим": один пользователь может состоять
# в нескольких командах, и одна команда может включать нескольких пользователей.
user_team_association = Table(
    "user_team_members",
    Base.metadata,
    Column("user_id", ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    Column("team_id", ForeignKey("teams.id", ondelete="CASCADE"), primary_key=True),
)


class Team(Base):
    """Команда (подразделение) — группа сотрудников под одним руководителем.

    Руководитель видит данные всех участников своей команды в режиме чтения.
    Один пользователь может быть в нескольких командах.
    """

    __tablename__ = "teams"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(String(512), nullable=True)

    # Поле manager_id хранит идентификатор руководителя команды.
    # Значение может быть пустым, если команда создана, но руководитель ещё не назначен.
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

    # Участники команды хранятся через отдельную таблицу связи.
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
